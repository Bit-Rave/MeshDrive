"""
Service pour gérer les fichiers chiffrés côté client (Zero-Knowledge)
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict
from fastapi import HTTPException, UploadFile

from cryptolib.chunk_manager import ChunkManager
from cryptolib.metadata_manager import MetadataManager
from cryptolib.models import EncryptedChunk
from core.database import User

logger = logging.getLogger(__name__)


class ClientEncryptedService:
    """Service pour gérer les fichiers déjà chiffrés côté client"""
    
    def __init__(self, user: User, chunks_dir: Path, keys_dir: Path):
        """
        Initialise le service
        
        Args:
            user: Utilisateur actuel
            chunks_dir: Répertoire des chunks
            keys_dir: Répertoire des clés
        """
        self.user = user
        self.chunk_manager = ChunkManager(chunks_dir)
        self.metadata_manager = MetadataManager(keys_dir)
    
    async def save_client_encrypted_file(
        self,
        encrypted_file_path: str,
        encrypted_key: str,
        nonce: str,
        integrity_hash: str,
        encrypted_metadata: str,
        original_size: int,
        folder_path: str = "/"
    ) -> Dict:
        """
        Sauvegarde un fichier déjà chiffré côté client
        
        Args:
            encrypted_file_path: Chemin vers le fichier chiffré temporaire
            encrypted_key: Clé chiffrée avec mot de passe utilisateur (base64)
            nonce: Nonce utilisé pour le chiffrement (base64)
            integrity_hash: Hash d'intégrité du fichier original (SHA-256)
            encrypted_metadata: Métadonnées chiffrées (base64)
            original_size: Taille originale du fichier
            folder_path: Chemin du dossier
            
        Returns:
            Dict avec file_id, original_name, chunks, folder_path
        """
        # Lire le fichier chiffré depuis le chemin temporaire
        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        encrypted_size = len(encrypted_data)
        
        # Générer un file_id basé sur le hash du fichier chiffré
        file_id = hashlib.sha256(encrypted_data).hexdigest()[:16]
        
        logger.info(f"📁 Sauvegarde fichier chiffré côté client: {file_id} (user: {self.user.id})")
        
        # Découper le fichier chiffré en chunks
        chunks = self.chunk_manager.split_into_chunks(encrypted_data, file_id)
        
        # Sauvegarder les métadonnées avec les clés chiffrées
        metadata = self.metadata_manager.save_metadata_client_encrypted(
            file_id=file_id,
            encrypted_key=encrypted_key,
            nonce=nonce,
            integrity_hash=integrity_hash,
            encrypted_metadata=encrypted_metadata,
            original_size=original_size,
            encrypted_size=encrypted_size,
            chunks=chunks,
            folder_path=folder_path
        )
        
        logger.info(f"✅ Fichier chiffré côté client sauvegardé: {file_id}")
        
        return {
            'file_id': file_id,
            'original_name': '[encrypted]',  # Nom chiffré côté client
            'chunks': [{
                'chunk_id': c.chunk_id,
                'hash': c.hash_sha256,
                'size': c.size,
                'index': c.index,
                'file_path': c.file_path
            } for c in chunks],
            'folder_path': folder_path,
            'encrypted_size': encrypted_size,
            'original_size': original_size
        }

