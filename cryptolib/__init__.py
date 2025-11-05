"""
Module core de MeshDrive - Système de chiffrement et gestion de fichiers
"""

import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des configurations
try:
    from .config import LOG_LEVEL, KEYS_DIR, CHUNKS_DIR, CHUNK_SIZE
except ImportError:
    # Valeurs par défaut si config.py n'existe pas
    LOG_LEVEL = "INFO"
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    KEYS_DIR = DATA_DIR / "keys"
    CHUNKS_DIR = DATA_DIR / "chunks"
    CHUNK_SIZE = 1024 * 1024
    
    # Créer les dossiers s'ils n'existent pas
    DATA_DIR.mkdir(exist_ok=True)
    KEYS_DIR.mkdir(exist_ok=True)
    CHUNKS_DIR.mkdir(exist_ok=True)

# Import des composants
from .chunk_manager import ChunkManager
from .metadata_manager import MetadataManager
from .folder_manager import FolderManager
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
        self.folder_manager = FolderManager(keys_dir)
        self.encryptor = Encryptor(self.chunk_manager, self.metadata_manager)
        self.decryptor = Decryptor(self.chunk_manager, self.metadata_manager)
    
    
    def encrypt_file(self, file_path: str, folder_path: str = "/", original_name: str = None):
        """Chiffre un fichier"""
        return self.encryptor.encrypt_file(file_path, folder_path, original_name)
    
    
    def decrypt_file(self, file_id: str, output_path: str = None):
        """Déchiffre un fichier"""
        return self.decryptor.decrypt_file(file_id, output_path)
    
    
    def list_files(self, folder_path: str = "/"):
        """Liste les fichiers chiffrés dans un dossier"""
        return self.metadata_manager.list_files(folder_path)
    
    
    def list_all_files(self):
        """Liste tous les fichiers chiffrés (tous dossiers confondus)"""
        return self.metadata_manager.list_all_files()
    
    
    def get_file_info(self, file_id: str):
        """Récupère les infos d'un fichier"""
        return self.metadata_manager.get_file_info(file_id)
    
    
    def move_file(self, file_id: str, new_folder_path: str) -> bool:
        """
        Déplace un fichier vers un nouveau dossier
        
        Args:
            file_id: ID du fichier à déplacer
            new_folder_path: Nouveau chemin du dossier
            
        Returns:
            True si le déplacement a réussi
        """
        # Vérifier que le fichier existe
        metadata = self.metadata_manager.load_metadata(file_id)
        
        # Vérifier que le dossier de destination existe (ou est la racine)
        if new_folder_path != "/":
            folder = self.folder_manager.get_folder(new_folder_path)
            if not folder:
                raise ValueError(f"❌ Dossier de destination introuvable: {new_folder_path}")
        
        # Mettre à jour le folder_path dans les métadonnées
        self.metadata_manager.update_file_folder_path(file_id, new_folder_path)
        
        logger.info(f"✅ Fichier déplacé: {file_id} -> {new_folder_path}")
        return True
    
    def delete_file(self, file_id: str, delete_chunks: bool = True):
        """Supprime un fichier"""
        if delete_chunks:
            metadata = self.metadata_manager.load_metadata(file_id)
            self.chunk_manager.delete_chunks(metadata['chunks'])
        
        self.metadata_manager.delete_metadata(file_id)
    
    
    # Méthodes pour les dossiers
    def create_folder(self, folder_name: str, parent_path: str = "/"):
        """Crée un nouveau dossier"""
        return self.folder_manager.create_folder(folder_name, parent_path)
    
    
    def list_folders(self, parent_path: str = "/"):
        """Liste les dossiers dans un dossier parent"""
        return self.folder_manager.list_folders(parent_path)
    
    
    def list_all_folders(self):
        """Liste tous les dossiers"""
        return self.folder_manager.list_all_folders()
    
    
    def get_folder(self, folder_path: str):
        """Récupère les métadonnées d'un dossier"""
        return self.folder_manager.get_folder(folder_path)
    
    
    def delete_folder(self, folder_path: str, recursive: bool = False):
        """Supprime un dossier et ses fichiers (chunks et keys)"""
        # Si récursif, supprimer d'abord les sous-dossiers
        if recursive:
            subfolders = self.folder_manager.list_folders(folder_path)
            for subfolder in subfolders:
                self.delete_folder(subfolder['folder_path'], recursive=True)
        
        # Supprimer tous les fichiers dans ce dossier
        files_in_folder = self.metadata_manager.list_files(folder_path)
        for file_info in files_in_folder:
            self.delete_file(file_info['file_id'], delete_chunks=True)
        
        # Supprimer le dossier lui-même
        return self.folder_manager.delete_folder(folder_path, recursive=False)
    
    
    def get_folder_contents(self, folder_path: str = "/"):
        """
        Récupère le contenu d'un dossier (fichiers et sous-dossiers)
        
        Returns:
            {
                'files': List[Dict],
                'folders': List[Dict]
            }
        """
        return {
            'files': self.list_files(folder_path),
            'folders': self.list_folders(folder_path)
        }


# Export
__all__ = ['CryptoSystem']

