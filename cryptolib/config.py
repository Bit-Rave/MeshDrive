"""Configuration globale du système de chiffrement"""

from pathlib import Path
from typing import Optional

# Répertoires de données (relatifs à la racine du projet)
# cryptolib/config.py -> parent = cryptolib/ -> parent.parent = racine du projet
# Utiliser resolve() pour s'assurer d'avoir un chemin absolu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Créer le dossier data s'il n'existe pas
DATA_DIR.mkdir(exist_ok=True)


def get_user_data_dir(user_id: int) -> Path:
    """Retourne le répertoire de données pour un utilisateur spécifique"""
    user_dir = DATA_DIR / "users" / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_keys_dir(user_id: int) -> Path:
    """Retourne le répertoire des clés pour un utilisateur spécifique"""
    keys_dir = get_user_data_dir(user_id) / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    return keys_dir


def get_user_chunks_dir(user_id: int) -> Path:
    """Retourne le répertoire des chunks pour un utilisateur spécifique"""
    chunks_dir = get_user_data_dir(user_id) / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    return chunks_dir


# Pour la compatibilité avec l'ancien code (sans user_id)
# Ces variables sont utilisées si user_id n'est pas fourni (déprécié)
KEYS_DIR = DATA_DIR / "keys"
CHUNKS_DIR = DATA_DIR / "chunks"

# Créer les dossiers s'ils n'existent pas (pour compatibilité)
KEYS_DIR.mkdir(exist_ok=True)
CHUNKS_DIR.mkdir(exist_ok=True)

# Taille des chunks (1 MB par défaut)
CHUNK_SIZE = 1024 * 1024

# Algorithme de chiffrement
ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_SIZE_BITS = 256
NONCE_SIZE_BITS = 96

# Logging
LOG_LEVEL = "INFO"
