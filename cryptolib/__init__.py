"""
Système de chiffrement pour MyDrive P2P
"""

import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import des configurations
try:
    from .config import LOG_LEVEL, KEYS_DIR, CHUNKS_DIR, CHUNK_SIZE
except ImportError:
    # Valeurs par défaut si config.py n'existe pas
    LOG_LEVEL = "INFO"
    KEYS_DIR = Path("./keys")
    CHUNKS_DIR = Path("./output")
    CHUNK_SIZE = 1024 * 1024

# Import des composants
from .chunk_manager import ChunkManager
from .metadata_manager import MetadataManager
from .encryptor import Encryptor
from .decryptor import Decryptor


class CryptoSystem:
    """
    Point d'entrée principal pour le chiffrement/déchiffrement
    """
    
    def __init__(self, keys_dir=None, chunks_dir=None, chunk_size=None):
        keys_dir = keys_dir or KEYS_DIR
        chunks_dir = chunks_dir or CHUNKS_DIR
        chunk_size = chunk_size or CHUNK_SIZE
        
        self.chunk_manager = ChunkManager(chunks_dir, chunk_size)
        self.metadata_manager = MetadataManager(keys_dir)
        self.encryptor = Encryptor(self.chunk_manager, self.metadata_manager)
        self.decryptor = Decryptor(self.chunk_manager, self.metadata_manager)
    
    
    def encrypt_file(self, file_path: str):
        """Chiffre un fichier"""
        return self.encryptor.encrypt_file(file_path)
    
    
    def decrypt_file(self, file_id: str, output_path: str = None):
        """Déchiffre un fichier"""
        return self.decryptor.decrypt_file(file_id, output_path)
    
    
    def list_files(self):
        """Liste les fichiers chiffrés"""
        return self.metadata_manager.list_files()
    
    
    def get_file_info(self, file_id: str):
        """Récupère les infos d'un fichier"""
        return self.metadata_manager.get_file_info(file_id)
    
    
    def delete_file(self, file_id: str, delete_chunks: bool = True):
        """Supprime un fichier"""
        if delete_chunks:
            metadata = self.metadata_manager.load_metadata(file_id)
            self.chunk_manager.delete_chunks(metadata['chunks'])
        
        self.metadata_manager.delete_metadata(file_id)


# Export
__all__ = ['CryptoSystem']
