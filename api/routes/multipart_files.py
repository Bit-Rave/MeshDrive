"""
Route spéciale pour l'upload multipart de plusieurs fichiers (encrypt-folder)
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Request, File, Form, HTTPException, Depends
from fastapi import UploadFile

from core.database import User, get_db
from core.utils import check_quota, update_user_quota
from api.dependencies.auth import get_current_user_from_multipart
from api.services.file_service import FileService
from api.dependencies.crypto import get_crypto_system
from cryptolib import CryptoSystem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])


def _encrypt_single_file(file_data: dict, crypto_system: CryptoSystem) -> dict:
    """
    Fonction helper pour chiffrer un fichier dans un thread
    
    Args:
        file_data: Dict contenant file, folder_path, tmp_path
        crypto_system: Instance de CryptoSystem
        
    Returns:
        Dict avec success, file_id, original_name, folder_path ou error
    """
    from api.utils.file_helpers import cleanup_temp_file
    
    try:
        file = file_data['file']
        folder_path = file_data['folder_path']
        tmp_path = file_data['tmp_path']
        
        # Chiffrer le fichier avec le nom original
        result = crypto_system.encrypt_file(tmp_path, folder_path, file.filename)
        
        # Extraire les informations
        if hasattr(result, 'file_id'):
            file_id = result.file_id
            original_name = result.original_name
        else:
            file_id = result.get('file_id', '')
            original_name = result.get('original_name', file.filename)
        
        return {
            'success': True,
            'file_id': file_id,
            'original_name': original_name,
            'folder_path': folder_path,
            'filename': file.filename
        }
    except Exception as e:
        return {
            'success': False,
            'filename': file_data['file'].filename,
            'error': str(e)
        }
    finally:
        # Supprimer le fichier temporaire
        cleanup_temp_file(file_data['tmp_path'])


@router.post("/encrypt-folder")
async def encrypt_folder(
    request: Request,
    folder_path: str = "/",
    files: List[UploadFile] = File(...),
    token: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_from_multipart),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Chiffre plusieurs fichiers (upload de dossier) avec multithreading
    
    Args:
        request: Objet Request pour accéder aux headers et FormData
        folder_path: Chemin du dossier de destination
        files: Liste des fichiers à uploader (multipart/form-data)
        token: Token JWT depuis FormData (si le header Authorization est bloqué)
        current_user: Utilisateur authentifié (via dependency spéciale)
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des fichiers chiffrés
    """
    from api.utils.file_helpers import save_uploaded_file, cleanup_temp_file
    
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni dans la requête"
        )
    
    try:
        logger.info(f"📁 Upload de {len(files)} fichiers dans {folder_path} (multithreading) (user: {current_user.id})")
        
        # Préparer les fichiers pour le traitement parallèle et vérifier les quotas
        file_tasks = []
        total_size = 0
        file_sizes = {}
        
        for file in files:
            try:
                # Sauvegarder temporairement le fichier pour obtenir sa taille
                tmp_path, file_size = await save_uploaded_file(file)
                file_sizes[file.filename] = file_size
                total_size += file_size
                
                # Vérifier le quota pour chaque fichier
                if not check_quota(current_user, file_size):
                    # Nettoyer les fichiers temporaires déjà créés
                    for task in file_tasks:
                        cleanup_temp_file(task['tmp_path'])
                    cleanup_temp_file(tmp_path)
                    raise HTTPException(
                        status_code=403,
                        detail=f"Quota de stockage dépassé pour {file.filename}. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Fichier: {file_size} bytes"
                    )
                
                file_tasks.append({
                    'file': file,
                    'folder_path': folder_path,
                    'tmp_path': tmp_path,
                    'file_size': file_size
                })
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Erreur lors de la préparation de {file.filename}: {str(e)}")
        
        # Vérifier le quota total
        if not check_quota(current_user, total_size):
            # Nettoyer les fichiers temporaires
            for task in file_tasks:
                cleanup_temp_file(task['tmp_path'])
            raise HTTPException(
                status_code=403,
                detail=f"Quota de stockage insuffisant pour tous les fichiers. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Total requis: {total_size} bytes"
            )
        
        # Traiter les fichiers en parallèle avec ThreadPoolExecutor
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_encrypt_single_file, task, crypto_system) for task in file_tasks]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        results.append({
                            'file_id': result['file_id'],
                            'original_name': result['original_name'],
                            'folder_path': result['folder_path']
                        })
                        # Mettre à jour le quota pour ce fichier
                        if result['filename'] in file_sizes:
                            file_size = file_sizes[result['filename']]
                            db = next(get_db())
                            try:
                                update_user_quota(db, current_user.id, file_size, is_upload=True)
                                logger.info(f"📊 Quota mis à jour pour {result['filename']}: +{file_size} bytes")
                            finally:
                                db.close()
                    else:
                        errors.append({
                            'filename': result['filename'],
                            'error': result['error']
                        })
                        logger.error(f"❌ Erreur lors du chiffrement de {result['filename']}: {result['error']}")
                except Exception as e:
                    logger.error(f"❌ Erreur dans le thread: {str(e)}")
                    errors.append({
                        'filename': 'unknown',
                        'error': str(e)
                    })
        
        return {
            'success': len(results),
            'errors': len(errors),
            'files': results,
            'error_details': errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload du dossier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

