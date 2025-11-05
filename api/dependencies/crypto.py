"""
Dependencies pour obtenir le système cryptographique
"""

from fastapi import Depends
from core.database import User
from core.auth import get_current_active_user
from core.utils import get_crypto_system_for_user
from cryptolib import CryptoSystem


def get_crypto_system(
    current_user: User = Depends(get_current_active_user)
) -> CryptoSystem:
    """
    Dépendance pour obtenir le système cryptographique de l'utilisateur actuel
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        Instance de CryptoSystem configurée pour cet utilisateur
    """
    return get_crypto_system_for_user(current_user)

