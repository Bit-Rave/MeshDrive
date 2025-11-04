"""Module de chiffrement"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .models import EncryptedChunk
from .chunk_manager import ChunkManager
from .metadata_manager import MetadataManager
from .config import KEY_SIZE_BITS


logger = logging.getLogger(__name__)


class Encryptor:
    """Gère le chiffrement des fichiers"""
    
    def __init__(self, chunk_manager: ChunkManager, metadata_manager: MetadataManager):
        self.chunk_manager = chunk_manager
        self.metadata_manager = metadata_manager
    
    
    def encrypt_file(self, file_path: str) -> Dict:
        """
        Chiffre un fichier complet
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            {
                'file_id': str,
                'original_name': str,
                'chunks': List[EncryptedChunk],
                'metadata': FileMetadata
            }
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"❌ Fichier introuvable: {file_path}")
        
        logger.info(f"🔐 Chiffrement: {file_path.name}")
        
        # 1. Lecture du fichier
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        
        original_size = len(plaintext)
        logger.info(f"  📄 Taille: {self._format_size(original_size)}")
        
        # 2. Génération clé + nonce
        key, nonce = self._generate_key_and_nonce()
        logger.info(f"  🔑 Clé générée")
        
        # 3. Chiffrement
        ciphertext = self._encrypt_data(plaintext, key, nonce)
        logger.info(f"  ✅ Données chiffrées: {self._format_size(len(ciphertext))}")
        
        # 4. Génération file_id
        file_id = self._generate_file_id(ciphertext)
        logger.info(f"  🆔 File ID: {file_id}")
        
        # 5. Découpage en chunks
        chunks = self.chunk_manager.split_into_chunks(ciphertext, file_id)
        
        # 6. Sauvegarde métadonnées
        metadata = self.metadata_manager.save_metadata(
            file_id=file_id,
            original_name=file_path.name,
            original_size=original_size,
            encrypted_size=len(ciphertext),
            key=key,
            nonce=nonce,
            chunks=chunks
        )
        
        logger.info(f"✅ Chiffrement terminé\n")
        
        return {
            'file_id': file_id,
            'original_name': file_path.name,
            'chunks': chunks,
            'metadata': metadata
        }
    
    
    def _generate_key_and_nonce(self):
        """Génère une clé AES-256 et un nonce"""
        key = AESGCM.generate_key(bit_length=KEY_SIZE_BITS)
        nonce = os.urandom(12)  # 96 bits pour AES-GCM
        return key, nonce
    
    
    def _encrypt_data(self, plaintext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Chiffre les données avec AES-256-GCM"""
        aesgcm = AESGCM(key)
        return aesgcm.encrypt(nonce, plaintext, associated_data=None)
    
    
    def _generate_file_id(self, data: bytes) -> str:
        """Génère un ID unique basé sur le hash"""
        return hashlib.sha256(data).hexdigest()[:16]
    
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formate la taille en human-readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
