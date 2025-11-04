"""Gestion des dossiers"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .models import FolderMetadata
from .config import KEYS_DIR


logger = logging.getLogger(__name__)


class FolderManager:
    """Gère la création, la sauvegarde et le chargement des dossiers"""
    
    def __init__(self, keys_dir: Path = KEYS_DIR):
        self.keys_dir = keys_dir
        self.folders_dir = keys_dir / "_folders"
        self.folders_dir.mkdir(parents=True, exist_ok=True)
    
    
    def create_folder(self, folder_name: str, parent_path: str = "/") -> FolderMetadata:
        """
        Crée un nouveau dossier
        
        Args:
            folder_name: Nom du dossier
            parent_path: Chemin du dossier parent (par défaut "/" pour la racine)
            
        Returns:
            Objet FolderMetadata
        """
        # Normaliser les chemins
        parent_path = self._normalize_path(parent_path)
        folder_name = folder_name.strip().strip("/")
        
        if not folder_name:
            raise ValueError("❌ Le nom du dossier ne peut pas être vide")
        
        # Construire le chemin complet
        if parent_path == "/":
            folder_path = f"/{folder_name}"
        else:
            folder_path = f"{parent_path}/{folder_name}"
        
        # Vérifier que le dossier n'existe pas déjà
        if self.folder_exists(folder_path):
            raise ValueError(f"❌ Le dossier existe déjà: {folder_path}")
        
        # Générer un ID unique pour le dossier
        folder_id = self._generate_folder_id(folder_path)
        
        # Créer les métadonnées
        folder = FolderMetadata(
            folder_id=folder_id,
            folder_name=folder_name,
            folder_path=folder_path,
            parent_path=parent_path,
            created_at=self._get_timestamp()
        )
        
        # Sauvegarder les métadonnées
        folder_path_file = self.folders_dir / f"{folder_id}.json"
        
        with open(folder_path_file, 'w') as f:
            json.dump({
                'folder_id': folder.folder_id,
                'folder_name': folder.folder_name,
                'folder_path': folder.folder_path,
                'parent_path': folder.parent_path,
                'created_at': folder.created_at
            }, f, indent=2)
        
        logger.info(f"📁 Dossier créé: {folder_path}")
        return folder
    
    
    def folder_exists(self, folder_path: str) -> bool:
        """Vérifie si un dossier existe"""
        folder_path = self._normalize_path(folder_path)
        
        for folder_file in self.folders_dir.glob("*.json"):
            with open(folder_file, 'r') as f:
                folder_data = json.load(f)
                if folder_data['folder_path'] == folder_path:
                    return True
        
        return False
    
    
    def get_folder(self, folder_path: str) -> Optional[Dict]:
        """
        Récupère les métadonnées d'un dossier
        
        Args:
            folder_path: Chemin du dossier
            
        Returns:
            Dictionnaire des métadonnées ou None si le dossier n'existe pas
        """
        folder_path = self._normalize_path(folder_path)
        
        for folder_file in self.folders_dir.glob("*.json"):
            with open(folder_file, 'r') as f:
                folder_data = json.load(f)
                if folder_data['folder_path'] == folder_path:
                    return folder_data
        
        return None
    
    
    def list_folders(self, parent_path: str = "/") -> List[Dict]:
        """
        Liste tous les dossiers dans un dossier parent
        
        Args:
            parent_path: Chemin du dossier parent
            
        Returns:
            Liste des dossiers
        """
        parent_path = self._normalize_path(parent_path)
        folders = []
        
        for folder_file in self.folders_dir.glob("*.json"):
            with open(folder_file, 'r') as f:
                folder_data = json.load(f)
                if folder_data['parent_path'] == parent_path:
                    folders.append({
                        'folder_id': folder_data['folder_id'],
                        'folder_name': folder_data['folder_name'],
                        'folder_path': folder_data['folder_path'],
                        'parent_path': folder_data['parent_path'],
                        'created_at': folder_data['created_at']
                    })
        
        return folders
    
    
    def list_all_folders(self) -> List[Dict]:
        """Liste tous les dossiers"""
        folders = []
        
        for folder_file in self.folders_dir.glob("*.json"):
            with open(folder_file, 'r') as f:
                folder_data = json.load(f)
                folders.append({
                    'folder_id': folder_data['folder_id'],
                    'folder_name': folder_data['folder_name'],
                    'folder_path': folder_data['folder_path'],
                    'parent_path': folder_data['parent_path'],
                    'created_at': folder_data['created_at']
                })
        
        return folders
    
    
    def delete_folder(self, folder_path: str, recursive: bool = False) -> bool:
        """
        Supprime un dossier
        
        Args:
            folder_path: Chemin du dossier à supprimer
            recursive: Si True, supprime aussi les sous-dossiers et fichiers
            
        Returns:
            True si le dossier a été supprimé, False sinon
        """
        folder_path = self._normalize_path(folder_path)
        
        # Vérifier si le dossier existe
        folder = self.get_folder(folder_path)
        if not folder:
            return False
        
        # Si récursif, supprimer les sous-dossiers et fichiers
        if recursive:
            # Supprimer les sous-dossiers
            subfolders = self.list_folders(folder_path)
            for subfolder in subfolders:
                self.delete_folder(subfolder['folder_path'], recursive=True)
            
            # Note: Les fichiers dans le dossier seront gérés par MetadataManager
        
        # Supprimer le fichier de métadonnées
        folder_file = self.folders_dir / f"{folder['folder_id']}.json"
        if folder_file.exists():
            folder_file.unlink()
            logger.info(f"🗑️  Dossier supprimé: {folder_path}")
            return True
        
        return False
    
    
    def get_folder_id(self, folder_path: str) -> Optional[str]:
        """Récupère l'ID d'un dossier depuis son chemin"""
        folder = self.get_folder(folder_path)
        if folder:
            return folder['folder_id']
        return None
    
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalise un chemin (supprime les doublons de /, etc.)"""
        if not path:
            return "/"
        
        # Supprimer les espaces en début/fin
        path = path.strip()
        
        # S'assurer que ça commence par /
        if not path.startswith("/"):
            path = "/" + path
        
        # Supprimer les doublons de /
        parts = [p for p in path.split("/") if p]
        normalized = "/" + "/".join(parts)
        
        return normalized
    
    
    @staticmethod
    def _generate_folder_id(folder_path: str) -> str:
        """Génère un ID unique pour un dossier"""
        return hashlib.sha256(folder_path.encode()).hexdigest()[:16]
    
    
    @staticmethod
    def _get_timestamp() -> str:
        """Retourne le timestamp ISO 8601"""
        return datetime.utcnow().isoformat() + 'Z'

