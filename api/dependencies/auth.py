"""
Dependencies d'authentification personnalisées
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, Form
from jose import JWTError, jwt
from core.auth import SECRET_KEY, ALGORITHM, TokenData, get_user_by_username
from core.database import get_db, User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def get_current_user_from_multipart(
    request: Request,
    token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance pour obtenir l'utilisateur actuel depuis une requête multipart/form-data
    
    Cette fonction gère l'extraction du token depuis:
    1. Le header Authorization (priorité)
    2. Le paramètre Form "token" (fallback)
    
    Args:
        request: Objet Request FastAPI
        token: Token JWT depuis FormData (optionnel)
        db: Session de base de données
        
    Returns:
        Objet User de l'utilisateur authentifié
        
    Raises:
        HTTPException: Si l'authentification échoue
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Récupérer le token depuis le header Authorization
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    final_token = None
    
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            final_token = parts[1]
            logger.debug("Token extrait depuis header Authorization")
    
    # Si pas de token dans le header, essayer depuis FormData
    if not final_token and token:
        final_token = token
        logger.debug("Token extrait depuis FormData (paramètre Form)")
    
    if not final_token:
        logger.error("Token manquant - Authorization header: {}, FormData token: {}".format(
            auth_header is not None, token is not None
        ))
        raise credentials_exception
    
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"Erreur JWT: {str(e)}")
        raise credentials_exception
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

