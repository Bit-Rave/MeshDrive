"""
Dependencies réutilisables pour l'API
"""

from .crypto import get_crypto_system
from .auth import get_current_user_from_multipart

__all__ = ['get_crypto_system', 'get_current_user_from_multipart']

