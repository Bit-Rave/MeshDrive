"""Gestion des métadonnées de fichiers chiffrés"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from .models import FileMetadata, EncryptedChunk
from .config import KEYS_DIR, ENCRYPTION_ALGORITHM, KEY_SIZE_BITS, NONCE_SIZE_BITS


logger = logging.getLogger(__name__)


class MetadataManager:
    """Gère la sauvegarde et le chargement des métadonnées"""
    
    def __init__(self, keys_dir: Path = KEYS_DIR):
        self.keys_dir = keys_dir
        self.keys_dir.mkdir(parents=True, exist_ok=True)
    
    
    def save_metadata(self, file_id: str, original_name: str,
                     original_size: int, encrypted_size: int,
                     key: bytes, nonce: bytes,
                     chunks: List[EncryptedChunk]) -> FileMetadata:
        """
        Sauvegarde les métadonnées d'un fichier chiffré
        
        Args:
            file_id: ID unique du fichier
            original_name: Nom original du fichier
            original_size: Taille originale
            encrypted_size: Taille chiffrée
            key: Clé de chiffrement
            nonce: Nonce utilisé
            chunks: Liste des chunks
            
        Returns:
            Objet FileMetadata
        """
        metadata = FileMetadata(
            file_id=file_id,
            original_name=original_name,
            original_size=original_size,
            encrypted_size=encrypted_size,
            key=key.hex(),
            nonce=nonce.hex(),
            chunks=[
                {
                    'chunk_id': c.chunk_id,
                    'hash': c.hash_sha256,
                    'size': c.size,
                    'index': c.index,
                    'file_path': c.file_path
                }
                for c in chunks
            ],
            created_at=self._get_timestamp()
        )
        
        metadata_path = self.keys_dir / f"{file_id}.json"
        
        with open(metadata_path, 'w') as f:
            json.dump({
                'file_id': metadata.file_id,
                'original_name': metadata.original_name,
                'original_size': metadata.original_size,
                'encrypted_size': metadata.encrypted_size,
                'encryption': {
                    'algorithm': ENCRYPTION_ALGORITHM,
                    'key': metadata.key,
                    'nonce': metadata.nonce,
                    'key_size_bits': KEY_SIZE_BITS,
                    'nonce_size_bits': NONCE_SIZE_BITS
                },
                'chunks': metadata.chunks,
                'created_at': metadata.created_at
            }, f, indent=2)
        
        logger.info(f"  💾 Métadonnées sauvegardées")
        return metadata
    
    
    def load_metadata(self, file_id: str) -> Dict:
        """
        Charge les métadonnées d'un fichier
        
        Args:
            file_id: ID du fichier
            
        Returns:
            Dictionnaire des métadonnées
        """
        metadata_path = self.keys_dir / f"{file_id}.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"❌ Métadonnées introuvables pour {file_id}\n"
                f"   Chemin: {metadata_path}\n"
                f"   Ce fichier n'a pas été chiffré sur cet ordinateur."
            )
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    
    def list_files(self) -> List[Dict]:
        """Liste tous les fichiers chiffrés"""
        files = []

        for metadata_file in self.keys_dir.glob("*.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                files.append({
                    'file_id': metadata['file_id'],
                    'original_name': metadata['original_name'],  # ✅ Changé
                    'file_size': metadata['original_size'],      # ✅ Changé
                    'chunk_count': len(metadata['chunks']),      # ✅ Changé
                    'upload_date': metadata['created_at']        # ✅ Changé
                })

        return files
        
    
    def get_file_info(self, file_id: str) -> Dict:
        """Récupère les informations d'un fichier"""
        metadata = self.load_metadata(file_id)
        
        return {
            'file_id': metadata['file_id'],
            'name': metadata['original_name'],
            'size': metadata['original_size'],
            'encrypted_size': metadata['encrypted_size'],
            'algorithm': metadata['encryption']['algorithm'],
            'chunks': len(metadata['chunks']),
            'created_at': metadata['created_at']
        }
    
    
    def delete_metadata(self, file_id: str):
        """Supprime les métadonnées d'un fichier"""
        metadata_path = self.keys_dir / f"{file_id}.json"
        
        if metadata_path.exists():
            metadata_path.unlink()
            logger.info(f"  ✅ Métadonnées supprimées")
        else:
            logger.warning(f"  ⚠️  Métadonnées introuvables")
    
    
    @staticmethod
    def _get_timestamp() -> str:
        """Retourne le timestamp ISO 8601"""
        return datetime.utcnow().isoformat() + 'Z'
