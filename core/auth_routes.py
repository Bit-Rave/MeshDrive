"""
Endpoints d'authentification
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    UserCreate,
    UserResponse,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user_by_username
)
from core.database import get_db, User
from core.security import log_action, get_client_ip, AuditAction

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel utilisateur
    """
    ip_address = get_client_ip(request)
    
    try:
        user = create_user(db, user_create)
        
        # Logger l'inscription réussie
        log_action(
            user_id=user.id,
            action=AuditAction.REGISTER,
            resource=user.username,
            success=True,
            details=f"Email: {user.email}",
            ip_address=ip_address
        )
        
        return UserResponse.model_validate(user)
    except HTTPException as e:
        # Logger l'échec d'inscription
        log_action(
            user_id=None,
            action=AuditAction.REGISTER,
            resource=user_create.username,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise
    except Exception as e:
        # Logger l'erreur
        log_action(
            user_id=None,
            action=AuditAction.REGISTER,
            resource=user_create.username,
            success=False,
            details=f"Error: {str(e)}",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne un token JWT
    """
    ip_address = get_client_ip(request)
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Logger la tentative de connexion échouée
        log_action(
            user_id=None,
            action=AuditAction.LOGIN,
            resource=form_data.username,
            success=False,
            details="Incorrect username or password",
            ip_address=ip_address
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Logger la connexion réussie
    log_action(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource=user.username,
        success=True,
        details=f"Token expires in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
        ip_address=ip_address
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Retourne les informations de l'utilisateur actuel
    """
    return UserResponse.model_validate(current_user)


@router.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les informations d'un utilisateur (admin uniquement ou soi-même)
    """
    if username != current_user.username and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

