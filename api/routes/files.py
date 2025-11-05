"""
Routes pour la gestion des fichiers
"""

import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from core.database import User
from core.auth import get_current_active_user
from cryptolib.models import EncryptResponse, DecryptResponse, FileDetails, FileInfo, MoveFileRequest
from api.dependencies.crypto import get_crypto_system
from api.services.file_service import FileService
from cryptolib import CryptoSystem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt_file(
    file: UploadFile = File(...),
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Chiffre un fichier uploadé
    
    Args:
        file: Fichier à chiffrer (multipart/form-data)
        folder_path: Chemin du dossier de destination
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Informations sur le fichier chiffré
    """
    service = FileService(crypto_system, current_user)
    return await service.encrypt_file(file, folder_path)


@router.get("/decrypt/{file_id}")
async def decrypt_file(
    file_id: str,
    download: bool = False,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Déchiffre un fichier
    
    Args:
        file_id: ID du fichier à déchiffrer
        download: Si True, télécharge le fichier. Si False, retourne le chemin
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Fichier déchiffré ou chemin du fichier
    """
    service = FileService(crypto_system, current_user)
    return service.decrypt_file(file_id, download)


@router.get("/files", response_model=List[FileInfo])
async def list_files(
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Liste tous les fichiers chiffrés dans un dossier
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Liste des fichiers avec leurs informations
    """
    service = FileService(crypto_system, current_user)
    return service.list_files(folder_path)


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
    file_id: str,
    request: MoveFileRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Déplace un fichier vers un nouveau dossier
    
    Args:
        file_id: ID du fichier à déplacer
        request: Requête contenant le nouveau chemin du dossier
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    service = FileService(crypto_system, current_user)
    return service.move_file(file_id, request.new_folder_path)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    delete_chunks: bool = True,
    current_user: User = Depends(get_current_active_user),
    crypto_system: CryptoSystem = Depends(get_crypto_system)
):
    """
    Supprime un fichier
    
    Args:
        file_id: ID du fichier à supprimer
        delete_chunks: Si True, supprime aussi les chunks
        current_user: Utilisateur authentifié
        crypto_system: Système cryptographique de l'utilisateur
        
    Returns:
        Message de confirmation
    """
    service = FileService(crypto_system, current_user)
    return service.delete_file(file_id, delete_chunks)

