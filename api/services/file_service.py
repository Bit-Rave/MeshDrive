"""
Service métier pour la gestion des fichiers
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from cryptolib import CryptoSystem
from cryptolib.models import EncryptResponse, DecryptResponse, FileDetails, FileInfo
from core.database import User, get_db
from core.utils import check_quota, update_user_quota

logger = logging.getLogger(__name__)


class FileService:
    """Service pour les opérations sur les fichiers"""
    
    def __init__(self, crypto_system: CryptoSystem, user: User):
        """
        Initialise le service
        
        Args:
            crypto_system: Instance de CryptoSystem
            user: Utilisateur actuel
        """
        self.crypto_system = crypto_system
        self.user = user
    
    async def encrypt_file(
        self,
        file: UploadFile,
        folder_path: str = "/"
    ) -> EncryptResponse:
        """
        Chiffre un fichier uploadé
        
        Args:
            file: Fichier à chiffrer
            folder_path: Chemin du dossier de destination
            
        Returns:
            Informations sur le fichier chiffré
            
        Raises:
            HTTPException: Si le quota est dépassé ou en cas d'erreur
        """
        from api.utils.file_helpers import save_uploaded_file, cleanup_temp_file
        
        logger.info(f"🔐 Début du chiffrement: {file.filename} (user: {self.user.id})")
        
        # Sauvegarder le fichier temporairement
        tmp_path, file_size = await save_uploaded_file(file)
        
        try:
            # Vérifier le quota
            if not check_quota(self.user, file_size):
                raise HTTPException(
                    status_code=403,
                    detail=f"Quota de stockage dépassé. Utilisé: {self.user.used_bytes}/{self.user.quota_bytes} bytes. Fichier: {file_size} bytes"
                )
            
            # Chiffrer le fichier
            result = self.crypto_system.encrypt_file(tmp_path, folder_path, file.filename)
            
            # Extraire les informations
            if hasattr(result, 'file_id'):
                file_id = result.file_id
                original_name = result.original_name
                chunk_count = len(result.chunks) if hasattr(result, 'chunks') else 0
                result_folder_path = getattr(result, 'folder_path', folder_path)
            else:
                file_id = result.get('file_id', '')
                original_name = result.get('original_name', file.filename)
                chunks = result.get('chunks', [])
                chunk_count = len(chunks)
                result_folder_path = result.get('folder_path', folder_path)
            
            logger.info(f"✅ Chiffrement réussi: {file_id}")
            
            # Mettre à jour le quota
            db = next(get_db())
            try:
                update_user_quota(db, self.user.id, file_size, is_upload=True)
                logger.info(f"📊 Quota mis à jour: {self.user.used_bytes + file_size}/{self.user.quota_bytes} bytes")
            finally:
                db.close()
            
            return EncryptResponse(
                file_id=file_id,
                original_name=original_name,
                chunk_count=chunk_count,
                folder_path=result_folder_path,
                message="Fichier chiffré avec succès"
            )
        finally:
            cleanup_temp_file(tmp_path)
    
    def decrypt_file(
        self,
        file_id: str,
        download: bool = False
    ) -> FileResponse | DecryptResponse:
        """
        Déchiffre un fichier
        
        Args:
            file_id: ID du fichier à déchiffrer
            download: Si True, retourne un FileResponse. Sinon, retourne DecryptResponse
            
        Returns:
            FileResponse ou DecryptResponse
            
        Raises:
            HTTPException: Si le fichier n'existe pas ou en cas d'erreur
        """
        logger.info(f"🔓 Début du déchiffrement: {file_id} (user: {self.user.id})")
        
        # Obtenir les informations du fichier
        file_info = self.crypto_system.get_file_info(file_id)
        original_name = file_info.get('name', f"file_{file_id}")
        
        # Créer un fichier temporaire
        suffix = Path(original_name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Déchiffrer le fichier
            output_path = self.crypto_system.decrypt_file(file_id, tmp_path)
            
            logger.info(f"✅ Déchiffrement réussi: {output_path}")
            
            if download:
                return FileResponse(
                    output_path,
                    filename=original_name,
                    media_type='application/octet-stream'
                )
            else:
                return DecryptResponse(
                    file_id=file_id,
                    original_name=original_name,
                    output_path=output_path,
                    message="Fichier déchiffré avec succès"
                )
        except FileNotFoundError as e:
            cleanup_temp_file(tmp_path)
            logger.error(f"❌ Fichier introuvable: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
        except Exception as e:
            cleanup_temp_file(tmp_path)
            logger.error(f"❌ Erreur lors du déchiffrement: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erreur lors du déchiffrement: {str(e)}")
    
    def list_files(self, folder_path: str = "/") -> list[FileInfo]:
        """
        Liste les fichiers dans un dossier
        
        Args:
            folder_path: Chemin du dossier
            
        Returns:
            Liste des fichiers
        """
        files = self.crypto_system.list_files(folder_path)
        logger.info(f"📋 Liste de {len(files)} fichiers dans {folder_path}")
        return files
    
    def get_file_info(self, file_id: str) -> FileDetails:
        """
        Récupère les informations détaillées d'un fichier
        
        Args:
            file_id: ID du fichier
            
        Returns:
            Détails du fichier
            
        Raises:
            HTTPException: Si le fichier n'existe pas
        """
        try:
            file_info = self.crypto_system.get_file_info(file_id)
            
            # S'assurer que tous les champs sont présents
            return FileDetails(
                file_id=file_info.get('file_id', file_id),
                name=file_info.get('name', ''),
                size=file_info.get('size', 0),
                encrypted_size=file_info.get('encrypted_size', 0),
                algorithm=file_info.get('algorithm', 'AES-256-GCM'),
                chunks=file_info.get('chunks', 0),  # Déjà un int, pas besoin de len()
                created_at=file_info.get('created_at', '')
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
        except KeyError as e:
            logger.error(f"Erreur lors de la récupération des détails du fichier {file_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des détails: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des détails du fichier {file_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des détails: {str(e)}")
    
    def move_file(self, file_id: str, new_folder_path: str) -> dict:
        """
        Déplace un fichier vers un nouveau dossier
        
        Args:
            file_id: ID du fichier
            new_folder_path: Nouveau chemin du dossier
            
        Returns:
            Message de succès
            
        Raises:
            HTTPException: Si le fichier ou le dossier n'existe pas
        """
        try:
            self.crypto_system.move_file(file_id, new_folder_path)
            return {
                "message": "Fichier déplacé avec succès",
                "file_id": file_id,
                "new_folder_path": new_folder_path
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    
    def delete_file(self, file_id: str, delete_chunks: bool = True) -> dict:
        """
        Supprime un fichier
        
        Args:
            file_id: ID du fichier
            delete_chunks: Si True, supprime aussi les chunks
            
        Returns:
            Message de succès
            
        Raises:
            HTTPException: Si le fichier n'existe pas
        """
        try:
            # Obtenir les informations du fichier pour mettre à jour le quota
            file_info = self.crypto_system.get_file_info(file_id)
            file_size = file_info.get('size', 0)
            
            # Supprimer le fichier
            self.crypto_system.delete_file(file_id, delete_chunks)
            
            # Mettre à jour le quota
            if file_size > 0:
                db = next(get_db())
                try:
                    update_user_quota(db, self.user.id, file_size, is_upload=False)
                    logger.info(f"📊 Quota mis à jour: -{file_size} bytes")
                finally:
                    db.close()
            
            logger.info(f"🗑️  Fichier supprimé: {file_id}")
            return {
                "message": "Fichier supprimé avec succès",
                "file_id": file_id
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")

