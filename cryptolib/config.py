"""Configuration globale du système de chiffrement"""

from pathlib import Path

# Répertoires de données (relatifs à la racine du projet)
# cryptolib/config.py -> parent = cryptolib/ -> parent.parent = racine du projet
# Utiliser resolve() pour s'assurer d'avoir un chemin absolu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = DATA_DIR / "keys"
CHUNKS_DIR = DATA_DIR / "chunks"

# Créer les dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)
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
