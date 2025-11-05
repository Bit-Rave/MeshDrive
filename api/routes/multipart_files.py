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
from core.security import (
    validate_and_sanitize_folder_path,
    validate_and_sanitize_filename,
    validate_file_size,
    log_user_action,
    get_client_ip,
    AuditAction,
)
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
    client_encrypted: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_from_multipart),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Chiffre plusieurs fichiers (upload de dossier) avec multithreading
    OU accepte des fichiers déjà chiffrés côté client (Zero-Knowledge)
    
    Args:
        request: Objet Request pour accéder aux headers et FormData
        folder_path: Chemin du dossier de destination
        files: Liste des fichiers à uploader (multipart/form-data)
        token: Token JWT depuis FormData (si le header Authorization est bloqué)
        client_encrypted: Si "true", les fichiers sont déjà chiffrés côté client
        current_user: Utilisateur authentifié (via dependency spéciale)
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des fichiers chiffrés
    """
    from api.utils.file_helpers import save_uploaded_file, cleanup_temp_file
    from cryptolib.config import get_user_chunks_dir, get_user_keys_dir
    from api.services.client_encrypted_service import ClientEncryptedService
    
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni dans la requête"
        )
    
    ip_address = get_client_ip(request)
    
    # Vérifier si les fichiers sont déjà chiffrés côté client
    is_client_encrypted = client_encrypted == 'true'
    
    try:
        # Valider et sanitiser le chemin du dossier
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        if is_client_encrypted:
            logger.info(f"📁 Upload de {len(files)} fichiers CHIFFRÉS CÔTÉ CLIENT dans {folder_path} (Zero-Knowledge) (user: {current_user.id})")
            return await _handle_client_encrypted_files(request, files, folder_path, current_user, ip_address)
        else:
            logger.info(f"📁 Upload de {len(files)} fichiers dans {folder_path} (multithreading) (user: {current_user.id})")
        
        # Préparer les fichiers pour le traitement parallèle et vérifier les quotas
        file_tasks = []
        total_size = 0
        file_sizes = {}
        
        for file in files:
            # Valider et sanitiser le nom du fichier
            if file.filename:
                try:
                    file.filename = validate_and_sanitize_filename(file.filename)
                except HTTPException as e:
                    log_user_action(
                        current_user,
                        AuditAction.INVALID_FILENAME,
                        resource=file.filename,
                        success=False,
                        details=str(e.detail),
                        ip_address=ip_address
                    )
                    raise
            
            # Valider la taille du fichier (première vérification)
            try:
                validate_file_size(file)
            except HTTPException as e:
                log_user_action(
                    current_user,
                    AuditAction.FILE_TOO_LARGE,
                    resource=file.filename,
                    success=False,
                    details=str(e.detail),
                    ip_address=ip_address
                )
                raise
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
                    
                    # Logger l'échec de quota
                    log_user_action(
                        current_user,
                        AuditAction.QUOTA_EXCEEDED,
                        resource=file.filename,
                        success=False,
                        details=f"Quota dépassé: {current_user.used_bytes}/{current_user.quota_bytes} bytes, Fichier: {file_size} bytes",
                        ip_address=ip_address
                    )
                    
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
            
            # Logger l'échec de quota
            log_user_action(
                current_user,
                AuditAction.QUOTA_EXCEEDED,
                resource=f"{len(files)} fichiers",
                success=False,
                details=f"Quota insuffisant: {current_user.used_bytes}/{current_user.quota_bytes} bytes, Total requis: {total_size} bytes",
                ip_address=ip_address
            )
            
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
        
        # Logger l'action
        if len(results) > 0:
            log_user_action(
                current_user,
                AuditAction.FILE_UPLOAD,
                resource=f"{len(results)} fichiers",
                success=True,
                details=f"Folder: {folder_path}, Success: {len(results)}, Errors: {len(errors)}",
                ip_address=ip_address
            )
        elif len(errors) > 0:
            log_user_action(
                current_user,
                AuditAction.FILE_UPLOAD,
                resource=f"{len(files)} fichiers",
                success=False,
                details=f"All files failed: {errors}",
                ip_address=ip_address
            )
        
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
        
        # Logger l'erreur
        log_user_action(
            current_user,
            AuditAction.FILE_UPLOAD,
            resource=f"{len(files)} fichiers",
            success=False,
            details=f"Erreur: {str(e)}",
            ip_address=ip_address
        )
        
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


async def _handle_client_encrypted_files(
    request: Request,
    files: List[UploadFile],
    folder_path: str,
    current_user: User,
    ip_address: str
) -> dict:
    """
    Gère les fichiers déjà chiffrés côté client (Zero-Knowledge)
    
    Args:
        request: Objet Request pour accéder au FormData
        files: Liste des fichiers chiffrés
        folder_path: Chemin du dossier
        current_user: Utilisateur authentifié
        ip_address: Adresse IP du client
        
    Returns:
        Dict avec success, errors, files, error_details
    """
    from api.utils.file_helpers import save_uploaded_file, cleanup_temp_file
    from cryptolib.config import get_user_chunks_dir, get_user_keys_dir
    from api.services.client_encrypted_service import ClientEncryptedService
    from core.database import get_db
    from core.utils import check_quota, update_user_quota
    
    # Lire le FormData pour obtenir les métadonnées de chiffrement
    form_data = await request.form()
    
    # Créer le service pour les fichiers chiffrés côté client
    chunks_dir = get_user_chunks_dir(current_user.id)
    keys_dir = get_user_keys_dir(current_user.id)
    service = ClientEncryptedService(current_user, chunks_dir, keys_dir)
    
    results = []
    errors = []
    file_tasks = []
    
    try:
        # Préparer les fichiers et vérifier les quotas
        for index, file in enumerate(files):
            try:
                # Récupérer les métadonnées de chiffrement depuis FormData
                encrypted_key = form_data.get(f'file_key_{index}')
                nonce = form_data.get(f'file_nonce_{index}')
                integrity_hash = form_data.get(f'file_integrity_{index}')
                encrypted_metadata = form_data.get(f'file_metadata_{index}')
                original_size_str = form_data.get(f'file_original_size_{index}')
                
                if not all([encrypted_key, nonce, integrity_hash, encrypted_metadata, original_size_str]):
                    errors.append({
                        'filename': file.filename,
                        'error': f'Métadonnées de chiffrement manquantes pour le fichier {index}'
                    })
                    continue
                
                try:
                    original_size = int(original_size_str)
                except ValueError:
                    errors.append({
                        'filename': file.filename,
                        'error': f'Taille originale invalide: {original_size_str}'
                    })
                    continue
                
                # Vérifier le quota (utiliser la taille originale)
                if not check_quota(current_user, original_size):
                    errors.append({
                        'filename': file.filename,
                        'error': f'Quota de stockage dépassé. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Fichier: {original_size} bytes'
                    })
                    continue
                
                # Sauvegarder temporairement le fichier chiffré
                tmp_path, encrypted_file_size = await save_uploaded_file(file)
                
                file_tasks.append({
                    'file': file,
                    'tmp_path': tmp_path,
                    'encrypted_key': encrypted_key,
                    'nonce': nonce,
                    'integrity_hash': integrity_hash,
                    'encrypted_metadata': encrypted_metadata,
                    'original_size': original_size,
                    'encrypted_size': encrypted_file_size,
                    'folder_path': folder_path,
                    'index': index
                })
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la préparation du fichier {index}: {str(e)}")
                errors.append({
                    'filename': file.filename if file else f'file_{index}',
                    'error': str(e)
                })
        
        # Traiter les fichiers
        for task in file_tasks:
            try:
                # Sauvegarder le fichier chiffré côté client
                result = await service.save_client_encrypted_file(
                    encrypted_file_path=task['tmp_path'],
                    encrypted_key=task['encrypted_key'],
                    nonce=task['nonce'],
                    integrity_hash=task['integrity_hash'],
                    encrypted_metadata=task['encrypted_metadata'],
                    original_size=task['original_size'],
                    folder_path=task['folder_path']
                )
                
                results.append({
                    'file_id': result['file_id'],
                    'original_name': '[encrypted]',  # Nom chiffré côté client
                    'folder_path': result['folder_path']
                })
                
                # Mettre à jour le quota (utiliser la taille originale)
                db = next(get_db())
                try:
                    update_user_quota(db, current_user.id, task['original_size'], is_upload=True)
                    logger.info(f"📊 Quota mis à jour pour fichier chiffré: +{task['original_size']} bytes")
                finally:
                    db.close()
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la sauvegarde du fichier chiffré {task['index']}: {str(e)}")
                errors.append({
                    'filename': task['file'].filename if task['file'] else f'file_{task["index"]}',
                    'error': str(e)
                })
            finally:
                # Nettoyer le fichier temporaire
                from api.utils.file_helpers import cleanup_temp_file
                cleanup_temp_file(task['tmp_path'])
        
        # Logger l'action
        if len(results) > 0:
            log_user_action(
                current_user,
                AuditAction.FILE_UPLOAD,
                resource=f"{len(results)} fichiers (Zero-Knowledge)",
                success=True,
                details=f"Folder: {folder_path}, Success: {len(results)}, Errors: {len(errors)}",
                ip_address=ip_address
            )
        elif len(errors) > 0:
            log_user_action(
                current_user,
                AuditAction.FILE_UPLOAD,
                resource=f"{len(files)} fichiers (Zero-Knowledge)",
                success=False,
                details=f"All files failed: {errors}",
                ip_address=ip_address
            )
        
        return {
            'success': len(results),
            'errors': len(errors),
            'files': results,
            'error_details': errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload des fichiers chiffrés côté client: {str(e)}")
        
        # Nettoyer les fichiers temporaires
        for task in file_tasks:
            from api.utils.file_helpers import cleanup_temp_file
            cleanup_temp_file(task.get('tmp_path'))
        
        # Logger l'erreur
        log_user_action(
            current_user,
            AuditAction.FILE_UPLOAD,
            resource=f"{len(files)} fichiers (Zero-Knowledge)",
            success=False,
            details=f"Erreur: {str(e)}",
            ip_address=ip_address
        )
        
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

