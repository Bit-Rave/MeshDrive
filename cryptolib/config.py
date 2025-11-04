"""Configuration globale du système de chiffrement"""

from pathlib import Path

# Répertoires
KEYS_DIR = Path("./keys")
CHUNKS_DIR = Path("./output")

# Taille des chunks (1 MB par défaut)
CHUNK_SIZE = 1024 * 1024

# Algorithme de chiffrement
ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_SIZE_BITS = 256
NONCE_SIZE_BITS = 96

# Logging
LOG_LEVEL = "INFO"
