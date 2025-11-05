"""
Routes pour la gestion des dossiers
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from core.database import User
from core.auth import get_current_active_user
from cryptolib.models import FolderInfo, FolderContentsResponse, CreateFolderRequest
from api.dependencies.crypto import get_crypto_system
from api.services.folder_service import FolderService
from cryptolib import CryptoSystem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["folders"])


@router.post("/folders", response_model=FolderInfo)
async def create_folder(
    request: CreateFolderRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Crée un nouveau dossier
    
    Args:
        request: Requête contenant le nom du dossier et le chemin parent
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Informations sur le dossier créé
    """
    service = FolderService(crypto_system)
    return service.create_folder(request)


@router.get("/folders", response_model=List[FolderInfo])
async def list_folders(
    parent_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Liste tous les dossiers dans un dossier parent
    
    Args:
        parent_path: Chemin du dossier parent (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des dossiers
    """
    service = FolderService(crypto_system)
    return service.list_folders(parent_path)


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
    folder_path: str,
    recursive: bool = False,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Supprime un dossier
    
    Args:
        folder_path: Chemin du dossier à supprimer
        recursive: Si True, supprime aussi les sous-dossiers et fichiers
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    service = FolderService(crypto_system)
    return service.delete_folder(folder_path, recursive)


@router.get("/folder-contents", response_model=FolderContentsResponse)
async def get_folder_contents(
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Récupère le contenu d'un dossier (fichiers et sous-dossiers)
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Contenu du dossier (fichiers et dossiers)
    """
    service = FolderService(crypto_system)
    return service.get_folder_contents(folder_path)


@router.get("/download-folder/{folder_path:path}")
async def download_folder_as_zip(
    folder_path: str,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Télécharge un dossier complet en ZIP avec multithreading pour le déchiffrement
    
    Args:
        folder_path: Chemin du dossier à télécharger (peut être "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Fichier ZIP contenant le dossier
    """
    service = FolderService(crypto_system)
    return service.download_folder_as_zip(folder_path)

