"""
Système d'authentification JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from core.database import get_db, User

# Configuration JWT
SECRET_KEY = "your-secret-key-change-this-in-production-please-use-a-long-random-string"  # TODO: Générer aléatoirement
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# Modèles Pydantic
class UserCreate(BaseModel):
    """Modèle pour créer un utilisateur"""
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Modèle de réponse pour un utilisateur"""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    quota_bytes: int
    used_bytes: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Modèle de réponse pour un token"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Données contenues dans le token"""
    username: Optional[str] = None


# Fonctions utilitaires
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    # Bcrypt limite les mots de passe à 72 bytes
    # Tronquer si nécessaire pour la vérification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    # Utiliser bcrypt directement
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hache un mot de passe"""
    # Bcrypt limite les mots de passe à 72 bytes
    # Cette fonction ne devrait jamais être appelée avec un mot de passe > 72 bytes
    # car create_user() vérifie avant. Mais on tronque par sécurité.
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Tronquer à 72 bytes pour éviter l'erreur bcrypt
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    # Hacher le mot de passe avec bcrypt directement
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Récupère un utilisateur par son nom d'utilisateur"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Récupère un utilisateur par son email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Récupère un utilisateur par son ID"""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authentifie un utilisateur"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_user(db: Session, user_create: UserCreate) -> User:
    """Crée un nouvel utilisateur"""
    # Vérifier la longueur du mot de passe
    password_bytes = user_create.password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe est trop long (maximum 72 caractères). Veuillez utiliser un mot de passe plus court."
        )
    
    # Vérifier la longueur minimale
    if len(user_create.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 6 caractères"
        )
    
    # Vérifier si l'utilisateur existe déjà
    if get_user_by_username(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà utilisé"
        )
    if get_user_by_email(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    # Créer le nouvel utilisateur
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extrait le token depuis le header Authorization"""
    if not authorization:
        return None
    
    # Format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


async def get_current_user(
    request: Request,
    oauth_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dépendance FastAPI pour obtenir l'utilisateur actuel
    
    Utilise Request pour extraire le header Authorization (fonctionne avec multipart/form-data)
    et OAuth2PasswordBearer pour les autres requêtes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extraire le token depuis le header Authorization dans Request
    # Cela fonctionne pour les requêtes multipart/form-data
    token = None
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    
    # Si le token n'est pas dans le header, essayer de le récupérer depuis les paramètres de la requête
    # (pour les requêtes multipart/form-data où le navigateur peut bloquer le header Authorization)
    if not token:
        # Essayer de récupérer le token depuis les paramètres de la requête
        # Cela nécessite que le token soit passé dans FormData
        try:
            form_data = await request.form()
            token_from_form = form_data.get("token")
            if token_from_form:
                token = token_from_form
        except Exception:
            pass
    
    # Utiliser le token extrait depuis le header, depuis FormData, ou depuis OAuth2PasswordBearer
    # Le token depuis le header fonctionne pour multipart/form-data
    # OAuth2PasswordBearer fonctionne pour les autres requêtes
    final_token = token or oauth_token
    
    # Si le token est toujours None ou vide, lever une exception
    if not final_token:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Token manquant - Authorization header: {auth_header}, OAuth token: {oauth_token}")
        logger.error(f"Tous les headers: {list(request.headers.keys())}")
        raise credentials_exception
    
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        # Log pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur JWT: {str(e)}")
        raise credentials_exception
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dépendance pour obtenir l'utilisateur actif"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user

