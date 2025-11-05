"""
Module de validation de sécurité pour les entrées utilisateur
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile


# Constantes de validation
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB par défaut
MAX_FILENAME_LENGTH = 255
FORBIDDEN_CHARS = ['<', '>', ':', '"', '|', '?', '*', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']


def validate_path(path: str) -> bool:
    """
    Valide qu'un chemin est sûr (pas de path traversal)
    
    Args:
        path: Chemin à valider
        
    Returns:
        True si le chemin est valide, False sinon
    """
    if not path:
        return False
    
    # Normaliser le chemin
    path = path.strip()
    
    # Vérifier qu'il n'y a pas de .. ou de chemins absolus
    if ".." in path or path.startswith("/") or "\\" in path:
        return False
    
    # Vérifier les caractères interdits
    if re.search(r'[<>:"|?*\x00-\x1f]', path):
        return False
    
    # Vérifier qu'il n'y a pas de chemins absolus Windows
    if re.match(r'^[A-Za-z]:', path):
        return False
    
    return True


def validate_folder_path(folder_path: str) -> bool:
    """
    Valide un chemin de dossier (plus permissif que validate_path)
    
    Args:
        folder_path: Chemin du dossier à valider
        
    Returns:
        True si le chemin est valide, False sinon
    """
    if not folder_path:
        return True  # "/" par défaut
    
    # Normaliser
    folder_path = folder_path.strip()
    
    # Accepter "/" comme racine
    if folder_path == "/":
        return True
    
    # Vérifier qu'il commence par "/"
    if not folder_path.startswith("/"):
        return False
    
    # Vérifier qu'il n'y a pas de ..
    if ".." in folder_path:
        return False
    
    # Vérifier les caractères interdits
    if re.search(r'[<>:"|?*\x00-\x1f]', folder_path):
        return False
    
    # Vérifier qu'il n'y a pas de backslash
    if "\\" in folder_path:
        return False
    
    return True


def validate_filename(filename: str) -> bool:
    """
    Valide qu'un nom de fichier est sûr
    
    Args:
        filename: Nom de fichier à valider
        
    Returns:
        True si le nom de fichier est valide, False sinon
    """
    if not filename:
        return False
    
    # Longueur maximale
    if len(filename) > MAX_FILENAME_LENGTH:
        return False
    
    # Caractères interdits
    if any(char in filename for char in FORBIDDEN_CHARS):
        return False
    
    # Pas de chemins absolus
    if filename.startswith('/') or filename.startswith('\\'):
        return False
    
    # Pas de .. 
    if '..' in filename:
        return False
    
    # Pas de chemins Windows absolus
    if re.match(r'^[A-Za-z]:', filename):
        return False
    
    # Ne pas accepter les noms réservés Windows
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    if filename.upper().split('.')[0] in reserved_names:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Nettoie et normalise un nom de fichier
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
        
    Raises:
        ValueError: Si le nom de fichier ne peut pas être nettoyé
    """
    if not filename:
        raise ValueError("Le nom de fichier ne peut pas être vide")
    
    # Normaliser Unicode (NFKD décompose les caractères accentués)
    filename = unicodedata.normalize('NFKD', filename)
    
    # Supprimer les caractères de contrôle et les caractères non-ASCII problématiques
    # Garder les caractères ASCII imprimables et certains caractères Unicode
    filename = ''.join(c for c in filename if unicodedata.category(c)[0] != 'C' or c in [' ', '-', '_', '.'])
    
    # Remplacer les caractères interdits par des underscores
    for char in FORBIDDEN_CHARS:
        filename = filename.replace(char, '_')
    
    # Remplacer les espaces multiples par un seul underscore
    filename = re.sub(r'[-\s]+', '_', filename)
    
    # Supprimer les caractères non-alphanumériques en début/fin (sauf . pour les extensions)
    filename = re.sub(r'^[^\w.]+|[^\w.]+$', '', filename)
    
    # Limiter la longueur
    if len(filename) > MAX_FILENAME_LENGTH:
        # Garder l'extension si possible
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_len = MAX_FILENAME_LENGTH - len(ext) - 1
            filename = name[:max_name_len] + '.' + ext
        else:
            filename = filename[:MAX_FILENAME_LENGTH]
    
    # Vérifier qu'il reste quelque chose
    if not filename or filename == '.' or filename == '..':
        raise ValueError("Le nom de fichier ne peut pas être nettoyé valablement")
    
    return filename


def validate_file_size(file: UploadFile, max_size: Optional[int] = None) -> None:
    """
    Valide la taille d'un fichier uploadé
    
    Args:
        file: Fichier uploadé
        max_size: Taille maximale en bytes (par défaut MAX_FILE_SIZE)
        
    Raises:
        HTTPException: Si le fichier est trop volumineux
    """
    if max_size is None:
        max_size = MAX_FILE_SIZE
    
    # Vérifier si on peut obtenir la taille depuis le fichier
    if hasattr(file, 'size') and file.size:
        if file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Taille: {file.size} bytes, Maximum: {max_size} bytes ({max_size / (1024*1024):.1f} MB)"
            )
    
    # Si on ne peut pas obtenir la taille maintenant, on vérifiera lors de la sauvegarde
    # (certains fichiers peuvent être streamés)


def validate_and_sanitize_filename(filename: str) -> str:
    """
    Valide et sanitise un nom de fichier en une seule opération
    
    Args:
        filename: Nom de fichier à valider et nettoyer
        
    Returns:
        Nom de fichier validé et nettoyé
        
    Raises:
        HTTPException: Si le nom de fichier n'est pas valide
    """
    try:
        sanitized = sanitize_filename(filename)
        if not validate_filename(sanitized):
            raise ValueError("Le nom de fichier nettoyé n'est toujours pas valide")
        return sanitized
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Nom de fichier invalide: {str(e)}"
        )


def validate_and_sanitize_folder_path(folder_path: str) -> str:
    """
    Valide et normalise un chemin de dossier
    
    Args:
        folder_path: Chemin du dossier à valider
        
    Returns:
        Chemin de dossier validé et normalisé
        
    Raises:
        HTTPException: Si le chemin n'est pas valide
    """
    if not folder_path or folder_path.strip() == "":
        return "/"
    
    folder_path = folder_path.strip()
    
    if not validate_folder_path(folder_path):
        raise HTTPException(
            status_code=400,
            detail=f"Chemin de dossier invalide: {folder_path}. Les chemins ne peuvent pas contenir '..' ou des caractères interdits."
        )
    
    # Normaliser le chemin
    if not folder_path.startswith("/"):
        folder_path = "/" + folder_path
    
    # Supprimer les slashes doubles
    folder_path = re.sub(r'/+', '/', folder_path)
    
    # S'assurer qu'il ne se termine pas par un slash (sauf pour la racine)
    if folder_path != "/" and folder_path.endswith("/"):
        folder_path = folder_path[:-1]
    
    return folder_path

