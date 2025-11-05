"""
Helpers pour la gestion des fichiers uploadés
"""

import tempfile
import os
from pathlib import Path
from fastapi import UploadFile
from typing import Tuple


async def save_uploaded_file(file: UploadFile) -> Tuple[str, int]:
    """
    Sauvegarde un fichier uploadé dans un fichier temporaire
    
    Args:
        file: Fichier uploadé
        
    Returns:
        Tuple (chemin du fichier temporaire, taille du fichier)
    """
    suffix = Path(file.filename).suffix if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
        file_size = len(content)
    
    return tmp_path, file_size


def cleanup_temp_file(file_path: str) -> None:
    """
    Supprime un fichier temporaire
    
    Args:
        file_path: Chemin du fichier à supprimer
    """
    if os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except Exception as e:
            # Log l'erreur mais ne pas lever d'exception
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Impossible de supprimer le fichier temporaire {file_path}: {e}")

