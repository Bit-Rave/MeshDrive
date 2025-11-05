"""
Utilitaires pour l'API
"""

from cryptolib import CryptoSystem
from core.database import User
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_crypto_system_for_user(user: User) -> CryptoSystem:
    """
    Retourne une instance de CryptoSystem configurée pour un utilisateur spécifique
    
    Args:
        user: Objet User de la base de données
    
    Returns:
        Instance de CryptoSystem configurée pour cet utilisateur
    """
    return CryptoSystem(user_id=user.id)


def check_quota(user: User, file_size: int) -> bool:
    """
    Vérifie si l'utilisateur a assez d'espace pour uploader un fichier
    
    Args:
        user: Objet User de la base de données
        file_size: Taille du fichier en bytes
    
    Returns:
        True si l'utilisateur a assez d'espace, False sinon
    """
    return user.used_bytes + file_size <= user.quota_bytes


def update_user_quota(db: Session, user_id: int, file_size: int, is_upload: bool = True):
    """
    Met à jour le quota d'un utilisateur
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        file_size: Taille du fichier en bytes
        is_upload: True si c'est un upload (augmente used_bytes), False si c'est une suppression (diminue)
    """
    from core.database import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    if is_upload:
        user.used_bytes += file_size
    else:
        user.used_bytes = max(0, user.used_bytes - file_size)
    
    db.commit()
    db.refresh(user)

