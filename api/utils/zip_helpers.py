"""
Helpers pour la création de fichiers ZIP
"""

import tempfile
import zipfile
import os
from typing import Dict, List
from cryptolib import CryptoSystem


def decrypt_file_for_zip(file_data: dict, crypto_system: CryptoSystem) -> dict:
    """
    Déchiffre un fichier pour l'ajouter à un ZIP
    
    Args:
        file_data: Dict contenant file_id, zip_path, original_name
        crypto_system: Instance de CryptoSystem
        
    Returns:
        Dict avec success, output_path, zip_path, original_name ou error
    """
    try:
        file_id = file_data['file_id']
        zip_path_in_zip = file_data['zip_path']
        original_name = file_data['original_name']
        
        # Créer un fichier temporaire pour le déchiffrement
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            output_path = tmp_file.name
        
        crypto_system.decrypt_file(file_id, output_path)
        
        return {
            'success': True,
            'output_path': output_path,
            'zip_path': zip_path_in_zip,
            'original_name': original_name
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'original_name': file_data.get('original_name', 'unknown')
        }


def create_zip_from_files(
    files_data: List[Dict],
    zip_filename: str = "download.zip"
) -> str:
    """
    Crée un fichier ZIP à partir d'une liste de fichiers déchiffrés
    
    Args:
        files_data: Liste de dicts avec output_path, zip_path, original_name
        zip_filename: Nom du fichier ZIP à créer
        
    Returns:
        Chemin du fichier ZIP créé
    """
    # Créer un fichier ZIP temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
        zip_path = tmp_zip.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_data in files_data:
            if file_data.get('success'):
                output_path = file_data['output_path']
                zip_path_in_zip = file_data['zip_path']
                
                if os.path.exists(output_path):
                    zip_file.write(output_path, zip_path_in_zip)
    
    return zip_path

