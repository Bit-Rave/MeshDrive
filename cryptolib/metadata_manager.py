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
                     chunks: List[EncryptedChunk],
                     folder_path: str = "/") -> FileMetadata:
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
            created_at=self._get_timestamp(),
            folder_path=folder_path
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
                'created_at': metadata.created_at,
                'folder_path': metadata.folder_path
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
    
    
    def list_files(self, folder_path: str = "/") -> List[Dict]:
        """
        Liste tous les fichiers chiffrés dans un dossier
        
        Args:
            folder_path: Chemin du dossier (par défaut "/" pour la racine)
        """
        files = []
        folder_path = self._normalize_path(folder_path)

        for metadata_file in self.keys_dir.glob("*.json"):
            # Ignorer les fichiers de dossiers
            if metadata_file.parent.name == "_folders":
                continue
                
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                # Filtrer par dossier
                file_folder = metadata.get('folder_path', '/')
                if self._normalize_path(file_folder) == folder_path:
                    # Vérifier si c'est un fichier chiffré côté client
                    is_client_encrypted = metadata.get('encryption', {}).get('client_encrypted', False)
                    
                    # Si c'est un fichier chiffré côté client, utiliser un nom temporaire
                    # Le vrai nom sera déchiffré côté client
                    original_name = metadata.get('original_name', '[encrypted]')
                    
                    # Filtrer les fichiers avec .enc dans le nom (fichiers temporaires)
                    if original_name and original_name.endswith('.enc'):
                        continue  # Ignorer ce fichier
                    
                    files.append({
                        'file_id': metadata['file_id'],
                        'original_name': original_name if not is_client_encrypted else '[encrypted]',
                        'file_size': metadata.get('original_size', metadata.get('encrypted_size', 0)),
                        'chunk_count': len(metadata['chunks']),
                        'upload_date': metadata['created_at'],
                        'folder_path': metadata.get('folder_path', '/'),
                        'client_encrypted': is_client_encrypted  # Indicateur pour le frontend
                    })

        return files
    
    
    def list_all_files(self) -> List[Dict]:
        """Liste tous les fichiers chiffrés (tous dossiers confondus)"""
        files = []

        for metadata_file in self.keys_dir.glob("*.json"):
            # Ignorer les fichiers de dossiers
            if metadata_file.parent.name == "_folders":
                continue
                
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                files.append({
                    'file_id': metadata['file_id'],
                    'original_name': metadata['original_name'],
                    'file_size': metadata['original_size'],
                    'chunk_count': len(metadata['chunks']),
                    'upload_date': metadata['created_at'],
                    'folder_path': metadata.get('folder_path', '/')
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
    
    
    def update_file_folder_path(self, file_id: str, new_folder_path: str) -> bool:
        """
        Met à jour le folder_path d'un fichier
        
        Args:
            file_id: ID du fichier
            new_folder_path: Nouveau chemin du dossier
            
        Returns:
            True si la mise à jour a réussi
        """
        metadata_path = self.keys_dir / f"{file_id}.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"❌ Fichier introuvable: {file_id}")
        
        # Charger les métadonnées actuelles
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Normaliser le nouveau chemin
        new_folder_path = self._normalize_path(new_folder_path)
        
        # Mettre à jour le folder_path
        metadata['folder_path'] = new_folder_path
        
        # Sauvegarder les métadonnées mises à jour
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"  ✅ Chemin du fichier mis à jour: {file_id} -> {new_folder_path}")
        return True
    
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
    
    
    def save_metadata_client_encrypted(
        self,
        file_id: str,
        encrypted_key: str,
        nonce: str,
        integrity_hash: str,
        encrypted_metadata: str,
        original_size: int,
        encrypted_size: int,
        chunks: List[EncryptedChunk],
        folder_path: str = "/"
    ) -> FileMetadata:
        """
        Sauvegarde les métadonnées d'un fichier chiffré côté client (Zero-Knowledge)
        
        Args:
            file_id: ID unique du fichier
            encrypted_key: Clé chiffrée avec le mot de passe utilisateur (base64)
            nonce: Nonce utilisé pour le chiffrement (base64)
            integrity_hash: Hash d'intégrité du fichier original (SHA-256)
            encrypted_metadata: Métadonnées chiffrées (nom de fichier, etc.) (base64)
            original_size: Taille originale du fichier
            encrypted_size: Taille chiffrée du fichier
            chunks: Liste des chunks
            folder_path: Chemin du dossier
            
        Returns:
            Objet FileMetadata
        """
        metadata_path = self.keys_dir / f"{file_id}.json"
        
        # Sauvegarder les métadonnées avec les clés chiffrées
        metadata_data = {
            'file_id': file_id,
            'original_size': original_size,
            'encrypted_size': encrypted_size,
            'encryption': {
                'algorithm': ENCRYPTION_ALGORITHM,
                'key': encrypted_key,  # Clé chiffrée (pas en clair)
                'nonce': nonce,
                'key_size_bits': KEY_SIZE_BITS,
                'nonce_size_bits': NONCE_SIZE_BITS,
                'client_encrypted': True  # Indicateur que c'est chiffré côté client
            },
            'integrity_hash': integrity_hash,
            'encrypted_metadata': encrypted_metadata,  # Métadonnées chiffrées
            'chunks': [
                {
                    'chunk_id': c.chunk_id,
                    'hash': c.hash_sha256,
                    'size': c.size,
                    'index': c.index,
                    'file_path': c.file_path
                }
                for c in chunks
            ],
            'created_at': self._get_timestamp(),
            'folder_path': folder_path
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata_data, f, indent=2)
        
        logger.info(f"  💾 Métadonnées sauvegardées (Zero-Knowledge)")
        
        # Retourner un objet FileMetadata (sans les données sensibles)
        return FileMetadata(
            file_id=file_id,
            original_name="[encrypted]",  # Nom chiffré
            original_size=original_size,
            encrypted_size=encrypted_size,
            key=encrypted_key,  # Clé chiffrée
            nonce=nonce,
            chunks=[{
                'chunk_id': c.chunk_id,
                'hash': c.hash_sha256,
                'size': c.size,
                'index': c.index,
                'file_path': c.file_path
            } for c in chunks],
            created_at=metadata_data['created_at'],
            folder_path=folder_path
        )
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalise un chemin"""
        if not path:
            return "/"
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path
        parts = [p for p in path.split("/") if p]
        return "/" + "/".join(parts)
