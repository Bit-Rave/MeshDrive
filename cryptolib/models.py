"""Modèles de données pour le système de chiffrement"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pydantic import BaseModel


# Modèles dataclass pour le système de chiffrement
@dataclass
class EncryptedChunk:
    """Représente un chunk chiffré"""
    chunk_id: str
    data: bytes
    size: int
    index: int
    hash_sha256: str
    file_path: str


@dataclass
class FileMetadata:
    """Métadonnées du fichier chiffré"""
    file_id: str
    original_name: str
    original_size: int
    encrypted_size: int
    key: str  # hex
    nonce: str  # hex
    chunks: List[Dict]
    created_at: str
    folder_path: str = "/"  # Chemin du dossier parent (par défaut à la racine)


@dataclass
class FolderMetadata:
    """Métadonnées d'un dossier"""
    folder_id: str
    folder_name: str
    folder_path: str  # Chemin complet du dossier (ex: "/Documents/Projets")
    parent_path: str  # Chemin du dossier parent (ex: "/Documents" ou "/" pour la racine)
    created_at: str


# Modèles Pydantic pour l'API
class FileInfo(BaseModel):
    """Informations sur un fichier chiffré"""
    file_id: str
    original_name: str
    file_size: int
    chunk_count: int
    upload_date: str


class FileDetails(BaseModel):
    """Détails complets d'un fichier"""
    file_id: str
    name: str
    size: int
    encrypted_size: int
    algorithm: str
    chunks: int
    created_at: str


class EncryptResponse(BaseModel):
    """Réponse après chiffrement"""
    file_id: str
    original_name: str
    chunk_count: int
    folder_path: str
    message: str


class FolderInfo(BaseModel):
    """Informations sur un dossier"""
    folder_id: str
    folder_name: str
    folder_path: str
    parent_path: str
    created_at: str


class CreateFolderRequest(BaseModel):
    """Requête pour créer un dossier"""
    folder_name: str
    parent_path: str = "/"


class FolderContentsResponse(BaseModel):
    """Contenu d'un dossier"""
    folder_path: str
    files: List[FileInfo]
    folders: List[FolderInfo]


class MoveFileRequest(BaseModel):
    """Requête pour déplacer un fichier"""
    new_folder_path: str


class DecryptResponse(BaseModel):
    """Réponse après déchiffrement"""
    file_id: str
    original_name: str
    output_path: str
    message: str
