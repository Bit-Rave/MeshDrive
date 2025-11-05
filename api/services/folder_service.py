"""
Service métier pour la gestion des dossiers
"""

import logging
import tempfile
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from fastapi import HTTPException
from fastapi.responses import FileResponse

from cryptolib import CryptoSystem
from cryptolib.models import FolderInfo, FolderContentsResponse, CreateFolderRequest
from api.utils.zip_helpers import decrypt_file_for_zip, create_zip_from_files

logger = logging.getLogger(__name__)


class FolderService:
    """Service pour les opérations sur les dossiers"""
    
    def __init__(self, crypto_system: CryptoSystem):
        """
        Initialise le service
        
        Args:
            crypto_system: Instance de CryptoSystem
        """
        self.crypto_system = crypto_system
    
    def create_folder(self, request: CreateFolderRequest) -> FolderInfo:
        """
        Crée un nouveau dossier
        
        Args:
            request: Requête contenant le nom et le chemin parent
            
        Returns:
            Informations sur le dossier créé
            
        Raises:
            HTTPException: Si le dossier existe déjà ou en cas d'erreur
        """
        try:
            logger.info(f"📁 Création du dossier: {request.folder_name} dans {request.parent_path}")
            
            folder = self.crypto_system.create_folder(request.folder_name, request.parent_path)
            
            logger.info(f"✅ Dossier créé: {folder.folder_path}")
            
            return FolderInfo(
                folder_id=folder.folder_id,
                folder_name=folder.folder_name,
                folder_path=folder.folder_path,
                parent_path=folder.parent_path,
                created_at=folder.created_at
            )
        except ValueError as e:
            logger.error(f"❌ Erreur lors de la création du dossier: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def list_folders(self, parent_path: str = "/") -> List[FolderInfo]:
        """
        Liste les dossiers dans un dossier parent
        
        Args:
            parent_path: Chemin du dossier parent
            
        Returns:
            Liste des dossiers
        """
        folders = self.crypto_system.list_folders(parent_path)
        logger.info(f"📁 Liste de {len(folders)} dossiers dans {parent_path}")
        return folders
    
    def list_all_folders(self) -> List[FolderInfo]:
        """
        Liste tous les dossiers du système
        
        Returns:
            Liste de tous les dossiers
        """
        all_folders_raw = self.crypto_system.list_all_folders()
        
        # Valider et nettoyer les données
        all_folders = []
        for folder in all_folders_raw:
            if all(key in folder for key in ['folder_id', 'folder_name', 'folder_path', 'parent_path', 'created_at']):
                all_folders.append(FolderInfo(
                    folder_id=str(folder['folder_id']),
                    folder_name=str(folder['folder_name']),
                    folder_path=str(folder['folder_path']),
                    parent_path=str(folder['parent_path']),
                    created_at=str(folder['created_at'])
                ))
        
        logger.info(f"📁 Liste de {len(all_folders)} dossiers au total")
        return all_folders
    
    def get_folder(self, folder_path: str) -> FolderInfo:
        """
        Récupère les métadonnées d'un dossier
        
        Args:
            folder_path: Chemin du dossier
            
        Returns:
            Informations sur le dossier
            
        Raises:
            HTTPException: Si le dossier n'existe pas
        """
        folder = self.crypto_system.get_folder(folder_path)
        if not folder:
            raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
        
        logger.info(f"📁 Informations du dossier: {folder_path}")
        return folder
    
    def delete_folder(self, folder_path: str, recursive: bool = False) -> dict:
        """
        Supprime un dossier
        
        Args:
            folder_path: Chemin du dossier
            recursive: Si True, supprime aussi les sous-dossiers et fichiers
            
        Returns:
            Message de confirmation
            
        Raises:
            HTTPException: Si le dossier n'existe pas ou en cas d'erreur
        """
        # Vérifier que le dossier existe
        folder = self.crypto_system.get_folder(folder_path)
        if not folder:
            raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
        
        # Supprimer le dossier
        success = self.crypto_system.delete_folder(folder_path, recursive=recursive)
        
        if not success:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
        
        logger.info(f"🗑️  Dossier supprimé: {folder_path}")
        return {
            "message": "Dossier supprimé avec succès",
            "folder_path": folder_path
        }
    
    def get_folder_contents(self, folder_path: str = "/") -> FolderContentsResponse:
        """
        Récupère le contenu d'un dossier (fichiers et sous-dossiers)
        
        Args:
            folder_path: Chemin du dossier
            
        Returns:
            Contenu du dossier
        """
        contents = self.crypto_system.get_folder_contents(folder_path)
        logger.info(f"📁 Contenu du dossier {folder_path}: {len(contents['files'])} fichiers, {len(contents['folders'])} dossiers")
        return FolderContentsResponse(
            folder_path=folder_path,
            files=contents['files'],
            folders=contents['folders']
        )
    
    def download_folder_as_zip(self, folder_path: str) -> FileResponse:
        """
        Télécharge un dossier complet en ZIP avec multithreading pour le déchiffrement
        
        Args:
            folder_path: Chemin du dossier à télécharger
            
        Returns:
            Fichier ZIP contenant le dossier
            
        Raises:
            HTTPException: Si le dossier n'existe pas ou en cas d'erreur
        """
        logger.info(f"📦 Téléchargement du dossier en ZIP: {folder_path} (multithreading)")
        
        # Vérifier que le dossier existe (sauf pour la racine)
        if folder_path != "/":
            folder = self.crypto_system.get_folder(folder_path)
            if not folder:
                raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
            folder_name = folder['folder_name']
        else:
            folder_name = "root"
        
        # Créer un fichier ZIP temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            zip_path = tmp_zip.name
        
        try:
            # Collecter tous les fichiers récursivement
            all_files = []
            
            def collect_files(folder_path_inner: str, base_path: str = ""):
                """Collecte récursivement tous les fichiers du dossier"""
                contents = self.crypto_system.get_folder_contents(folder_path_inner)
                
                # Ajouter les fichiers
                for file_info in contents['files']:
                    zip_path_in_zip = f"{base_path}/{file_info['original_name']}" if base_path else file_info['original_name']
                    all_files.append({
                        'file_id': file_info['file_id'],
                        'original_name': file_info['original_name'],
                        'zip_path': zip_path_in_zip
                    })
                
                # Ajouter les sous-dossiers récursivement
                for subfolder in contents['folders']:
                    subfolder_base = f"{base_path}/{subfolder['folder_name']}" if base_path else subfolder['folder_name']
                    collect_files(subfolder['folder_path'], subfolder_base)
            
            collect_files(folder_path, "")
            
            logger.info(f"  📄 {len(all_files)} fichiers à déchiffrer en parallèle")
            
            # Déchiffrer les fichiers en parallèle
            decrypted_files = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(decrypt_file_for_zip, file_data, self.crypto_system)
                    for file_data in all_files
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result['success']:
                            decrypted_files.append(result)
                        else:
                            logger.warning(f"⚠️ Erreur lors du déchiffrement de {result.get('original_name', 'unknown')}: {result.get('error', 'unknown error')}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur dans le thread: {str(e)}")
            
            # Créer le ZIP
            zip_path_final = create_zip_from_files(decrypted_files, f"{folder_name}.zip")
            
            # Nettoyer les fichiers temporaires déchiffrés
            for decrypted_file in decrypted_files:
                if decrypted_file.get('success') and os.path.exists(decrypted_file['output_path']):
                    try:
                        os.unlink(decrypted_file['output_path'])
                    except Exception as e:
                        logger.warning(f"⚠️ Impossible de supprimer le fichier temporaire: {str(e)}")
            
            logger.info(f"  ✅ ZIP créé avec {len(decrypted_files)} fichiers")
            
            # Retourner le fichier ZIP
            return FileResponse(
                zip_path_final,
                filename=f"{folder_name}.zip",
                media_type='application/zip'
            )
        except Exception as e:
            # Nettoyer le fichier ZIP en cas d'erreur
            if os.path.exists(zip_path):
                try:
                    os.unlink(zip_path)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")

