"""Modèles de données pour le système de chiffrement"""

from dataclasses import dataclass
from typing import List, Dict, Optional

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
