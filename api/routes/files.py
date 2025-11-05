"""
Routes pour la gestion des fichiers
"""

import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from core.database import User
from core.auth import get_current_active_user
from core.security import (
    validate_and_sanitize_folder_path,
    validate_and_sanitize_filename,
    validate_file_size,
    log_user_action,
    get_client_ip,
    AuditAction,
)
from cryptolib.models import EncryptResponse, DecryptResponse, FileDetails, FileInfo, MoveFileRequest
from cryptolib import CryptoSystem
from api.dependencies.crypto import get_crypto_system
from api.services.file_service import FileService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt_file(
    request: Request,
    file: UploadFile = File(...),
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Chiffre un fichier uploadé
    
    Args:
        request: Objet Request pour obtenir l'IP
        file: Fichier à chiffrer (multipart/form-data)
        folder_path: Chemin du dossier de destination
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Informations sur le fichier chiffré
    """
    ip_address = get_client_ip(request)
    
    try:
        # Valider et sanitiser les entrées
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        if file.filename:
            file.filename = validate_and_sanitize_filename(file.filename)
        
        # Valider la taille du fichier
        validate_file_size(file)
        
        service = FileService(crypto_system, current_user)
        result = await service.encrypt_file(file, folder_path)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FILE_UPLOAD,
            resource=result.file_id if hasattr(result, 'file_id') else None,
            success=True,
            details=f"Filename: {file.filename}, Folder: {folder_path}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        if e.status_code == 413:
            log_user_action(
                current_user,
                AuditAction.FILE_TOO_LARGE,
                resource=file.filename,
                success=False,
                details=str(e.detail),
                ip_address=ip_address
            )
        elif e.status_code == 400:
            log_user_action(
                current_user,
                AuditAction.INVALID_FILENAME,
                resource=file.filename,
                success=False,
                details=str(e.detail),
                ip_address=ip_address
            )
        raise


@router.get("/client-decrypt/{file_id}")
async def get_client_encrypted_file_data(
    request: Request,
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Retourne les données chiffrées et métadonnées pour déchiffrement côté client (Zero-Knowledge)
    
    Args:
        request: Objet Request pour obtenir l'IP
        file_id: ID du fichier chiffré côté client
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        JSON avec encrypted_file (base64), encrypted_key, nonce, integrity_hash, encrypted_metadata
    """
    import base64
    from cryptolib.chunk_manager import ChunkManager
    from cryptolib.config import get_user_chunks_dir
    
    ip_address = get_client_ip(request)
    
    logger.info(f"🔓 Récupération données chiffrées côté client: {file_id} (user: {current_user.id})")
    
    try:
        # Charger les métadonnées
        metadata = crypto_system.metadata_manager.load_metadata(file_id)
        
        # Vérifier si c'est un fichier chiffré côté client
        if not metadata.get('encryption', {}).get('client_encrypted', False):
            raise HTTPException(
                status_code=400,
                detail="Ce fichier n'est pas chiffré côté client. Utilisez /decrypt/{file_id}"
            )
        
        # Charger les chunks chiffrés
        chunks_dir = get_user_chunks_dir(current_user.id)
        chunk_manager = ChunkManager(chunks_dir)
        chunks_data = chunk_manager.load_chunks_from_disk(metadata['chunks'])
        
        # Réassembler le fichier chiffré
        encrypted_data = chunk_manager.reassemble_chunks(chunks_data)
        
        # Retourner les données pour déchiffrement côté client
        return {
            'file_id': file_id,
            'encrypted_file': base64.b64encode(encrypted_data).decode('utf-8'),
            'encrypted_key': metadata['encryption']['key'],  # Clé déjà chiffrée
            'nonce': metadata['encryption']['nonce'],
            'integrity_hash': metadata.get('integrity_hash'),
            'encrypted_metadata': metadata.get('encrypted_metadata'),
            'original_size': metadata.get('original_size'),
            'encrypted_size': metadata.get('encrypted_size')
        }
        
    except FileNotFoundError as e:
        log_user_action(
            current_user,
            AuditAction.FILE_DOWNLOAD,
            resource=file_id,
            success=False,
            details=f"File not found: {str(e)}",
            ip_address=ip_address
        )
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données chiffrées: {str(e)}")
        log_user_action(
            current_user,
            AuditAction.FILE_DOWNLOAD,
            resource=file_id,
            success=False,
            details=f"Error: {str(e)}",
            ip_address=ip_address
        )
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/decrypt/{file_id}")
async def decrypt_file(
    request: Request,
    file_id: str,
    download: bool = False,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Déchiffre un fichier (serveur-side) ou retourne les données pour déchiffrement côté client
    
    Args:
        request: Objet Request pour obtenir l'IP
        file_id: ID du fichier à déchiffrer
        download: Si True, télécharge le fichier. Si False, retourne le chemin
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Fichier déchiffré ou chemin du fichier
    """
    ip_address = get_client_ip(request)
    
    try:
        # Vérifier si c'est un fichier chiffré côté client
        try:
            metadata = crypto_system.metadata_manager.load_metadata(file_id)
            if metadata.get('encryption', {}).get('client_encrypted', False):
                # Rediriger vers l'endpoint client-decrypt
                # (mais on ne peut pas rediriger dans une API REST, donc on retourne une erreur)
                raise HTTPException(
                    status_code=400,
                    detail="Ce fichier est chiffré côté client. Utilisez /api/client-decrypt/{file_id} pour obtenir les données de déchiffrement."
                )
        except FileNotFoundError:
            pass  # Continuer avec le déchiffrement serveur normal
        
        service = FileService(crypto_system, current_user)
        result = service.decrypt_file(file_id, download)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FILE_DOWNLOAD,
            resource=file_id,
            success=True,
            details=f"Download: {download}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FILE_DOWNLOAD,
            resource=file_id,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise


@router.get("/files", response_model=List[FileInfo])
async def list_files(
    request: Request,
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Liste tous les fichiers chiffrés dans un dossier
    
    Args:
        request: Objet Request pour obtenir l'IP
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des fichiers avec leurs informations
    """
    try:
        # Valider le chemin du dossier
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        service = FileService(crypto_system, current_user)
        return service.list_files(folder_path)
    except HTTPException as e:
        # Logger les tentatives de path traversal
        log_user_action(
            current_user,
            AuditAction.PATH_TRAVERSAL_ATTEMPT,
            resource=folder_path,
            success=False,
            details=str(e.detail),
            ip_address=get_client_ip(request)
        )
        raise


@router.get("/files/{file_id}", response_model=FileDetails)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Récupère les informations détaillées d'un fichier
    
    Args:
        file_id: ID du fichier
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Détails du fichier
    """
    service = FileService(crypto_system, current_user)
    return service.get_file_info(file_id)


@router.put("/files/{file_id}/move")
async def move_file(
    http_request: Request,
    file_id: str,
    request: MoveFileRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Déplace un fichier vers un nouveau dossier
    
    Args:
        http_request: Objet Request pour obtenir l'IP
        file_id: ID du fichier à déplacer
        request: Requête contenant le nouveau chemin du dossier
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    ip_address = get_client_ip(http_request)
    
    try:
        # Valider le nouveau chemin
        new_folder_path = validate_and_sanitize_folder_path(request.new_folder_path)
        
        service = FileService(crypto_system, current_user)
        result = service.move_file(file_id, new_folder_path)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FILE_MOVE,
            resource=file_id,
            success=True,
            details=f"New folder: {new_folder_path}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FILE_MOVE,
            resource=file_id,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise


@router.delete("/files/{file_id}")
async def delete_file(
    request: Request,
    file_id: str,
    delete_chunks: bool = True,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Supprime un fichier
    
    Args:
        request: Objet Request pour obtenir l'IP
        file_id: ID du fichier à supprimer
        delete_chunks: Si True, supprime aussi les chunks
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    ip_address = get_client_ip(request)
    
    try:
        service = FileService(crypto_system, current_user)
        result = service.delete_file(file_id, delete_chunks)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FILE_DELETE,
            resource=file_id,
            success=True,
            details=f"Delete chunks: {delete_chunks}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FILE_DELETE,
            resource=file_id,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise

