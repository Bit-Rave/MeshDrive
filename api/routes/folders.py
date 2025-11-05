"""
Routes pour la gestion des dossiers
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request

from core.database import User
from core.auth import get_current_active_user
from core.security import (
    validate_and_sanitize_folder_path,
    log_user_action,
    get_client_ip,
    AuditAction,
)
from cryptolib.models import FolderInfo, FolderContentsResponse, CreateFolderRequest
from cryptolib import CryptoSystem
from api.dependencies.crypto import get_crypto_system
from api.services.folder_service import FolderService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["folders"])


@router.post("/folders", response_model=FolderInfo)
async def create_folder(
    http_request: Request,
    request: CreateFolderRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Crée un nouveau dossier
    
    Args:
        http_request: Objet Request pour obtenir l'IP
        request: Requête contenant le nom du dossier et le chemin parent
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Informations sur le dossier créé
    """
    ip_address = get_client_ip(http_request)
    
    try:
        # Valider le chemin parent
        request.parent_path = validate_and_sanitize_folder_path(request.parent_path)
        
        service = FolderService(crypto_system)
        result = service.create_folder(request)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FOLDER_CREATE,
            resource=result.folder_path if hasattr(result, 'folder_path') else None,
            success=True,
            details=f"Folder name: {request.folder_name}, Parent: {request.parent_path}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FOLDER_CREATE,
            resource=request.parent_path,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise


@router.get("/folders", response_model=List[FolderInfo])
async def list_folders(
    request: Request,
    parent_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Liste tous les dossiers dans un dossier parent
    
    Args:
        request: Objet Request pour obtenir l'IP
        parent_path: Chemin du dossier parent (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des dossiers
    """
    try:
        # Valider le chemin parent
        parent_path = validate_and_sanitize_folder_path(parent_path)
        
        service = FolderService(crypto_system)
        return service.list_folders(parent_path)
    except HTTPException as e:
        # Logger les tentatives de path traversal
        log_user_action(
            current_user,
            AuditAction.PATH_TRAVERSAL_ATTEMPT,
            resource=parent_path,
            success=False,
            details=str(e.detail),
            ip_address=get_client_ip(request)
        )
        raise


@router.get("/folders-all", response_model=List[FolderInfo])
async def list_all_folders(
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Liste tous les dossiers du système
    
    Args:
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste de tous les dossiers
    """
    service = FolderService(crypto_system)
    return service.list_all_folders()


@router.get("/folders/{folder_path:path}", response_model=FolderInfo)
async def get_folder(
    folder_path: str,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Récupère les métadonnées d'un dossier
    
    Args:
        folder_path: Chemin du dossier
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Informations sur le dossier
    """
    service = FolderService(crypto_system)
    return service.get_folder(folder_path)


@router.delete("/folders/{folder_path:path}")
async def delete_folder(
    request: Request,
    folder_path: str,
    recursive: bool = False,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Supprime un dossier
    
    Args:
        request: Objet Request pour obtenir l'IP
        folder_path: Chemin du dossier à supprimer
        recursive: Si True, supprime aussi les sous-dossiers et fichiers
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    ip_address = get_client_ip(request)
    
    try:
        # Valider le chemin du dossier
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        service = FolderService(crypto_system)
        result = service.delete_folder(folder_path, recursive)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FOLDER_DELETE,
            resource=folder_path,
            success=True,
            details=f"Recursive: {recursive}",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FOLDER_DELETE,
            resource=folder_path,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise


@router.get("/folder-contents", response_model=FolderContentsResponse)
async def get_folder_contents(
    request: Request,
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Récupère le contenu d'un dossier (fichiers et sous-dossiers)
    
    Args:
        request: Objet Request pour obtenir l'IP
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Contenu du dossier (fichiers et dossiers)
    """
    try:
        # Valider le chemin du dossier
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        service = FolderService(crypto_system)
        return service.get_folder_contents(folder_path)
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


@router.get("/download-folder/{folder_path:path}")
async def download_folder_as_zip(
    request: Request,
    folder_path: str,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Télécharge un dossier complet en ZIP avec multithreading pour le déchiffrement
    
    Args:
        request: Objet Request pour obtenir l'IP
        folder_path: Chemin du dossier à télécharger (peut être "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Fichier ZIP contenant le dossier
    """
    ip_address = get_client_ip(request)
    
    try:
        # Valider le chemin du dossier
        folder_path = validate_and_sanitize_folder_path(folder_path)
        
        service = FolderService(crypto_system)
        result = service.download_folder_as_zip(folder_path)
        
        # Logger l'action réussie
        log_user_action(
            current_user,
            AuditAction.FOLDER_DOWNLOAD,
            resource=folder_path,
            success=True,
            details="Download as ZIP",
            ip_address=ip_address
        )
        
        return result
    except HTTPException as e:
        # Logger l'échec
        log_user_action(
            current_user,
            AuditAction.FOLDER_DOWNLOAD,
            resource=folder_path,
            success=False,
            details=str(e.detail),
            ip_address=ip_address
        )
        raise

