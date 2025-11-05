"""
Module de chiffrement des clés avec mot de passe utilisateur
Pour architecture zero-knowledge dans un datacenter décentralisé
"""

import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# Configuration
PBKDF2_ITERATIONS = 100000  # Nombre d'itérations pour PBKDF2
SALT_SIZE = 16  # Taille du salt en bytes


def derive_master_key(password: str, salt: bytes) -> bytes:
    """
    Dérive une clé maître depuis le mot de passe utilisateur
    
    Args:
        password: Mot de passe utilisateur
        salt: Salt pour la dérivation
        
    Returns:
        Clé maître (32 bytes pour Fernet)
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))
    return base64.urlsafe_b64encode(key)


def encrypt_file_key(file_key: bytes, user_password: str, salt: Optional[bytes] = None) -> str:
    """
    Chiffre une clé de fichier avec le mot de passe utilisateur
    
    Le serveur ne peut jamais déchiffrer cette clé sans le mot de passe.
    Architecture zero-knowledge garantie.
    
    Args:
        file_key: Clé de chiffrement du fichier (bytes)
        user_password: Mot de passe utilisateur
        salt: Salt optionnel (généré si None)
        
    Returns:
        String base64 contenant: salt (16 bytes) + clé chiffrée
    """
    # Générer un salt si non fourni
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    
    # Dériver la clé maître depuis le mot de passe
    master_key = derive_master_key(user_password, salt)
    
    # Chiffrer la clé de fichier avec Fernet (AES-128 en mode CBC)
    f = Fernet(master_key)
    encrypted_key = f.encrypt(file_key)
    
    # Retourner salt + clé chiffrée en base64
    combined = salt + encrypted_key
    return base64.b64encode(combined).decode('utf-8')


def decrypt_file_key(encrypted_key_data: str, user_password: str) -> bytes:
    """
    Déchiffre une clé de fichier avec le mot de passe utilisateur
    
    Args:
        encrypted_key_data: String base64 contenant salt + clé chiffrée
        user_password: Mot de passe utilisateur
        
    Returns:
        Clé de fichier déchiffrée (bytes)
        
    Raises:
        ValueError: Si le mot de passe est incorrect
    """
    try:
        # Décoder base64
        combined = base64.b64decode(encrypted_key_data.encode('utf-8'))
        
        # Extraire salt (16 premiers bytes) et clé chiffrée
        salt = combined[:SALT_SIZE]
        encrypted_key = combined[SALT_SIZE:]
        
        # Dériver la clé maître depuis le mot de passe
        master_key = derive_master_key(user_password, salt)
        
        # Déchiffrer la clé de fichier
        f = Fernet(master_key)
        file_key = f.decrypt(encrypted_key)
        
        return file_key
    except Exception as e:
        raise ValueError(f"Impossible de déchiffrer la clé de fichier. Mot de passe incorrect ou données corrompues: {str(e)}")


def encrypt_metadata(metadata: dict, user_password: str, salt: Optional[bytes] = None) -> str:
    """
    Chiffre les métadonnées sensibles (nom de fichier, chemin, etc.)
    
    Args:
        metadata: Dictionnaire contenant les métadonnées sensibles
        user_password: Mot de passe utilisateur
        salt: Salt optionnel (généré si None)
        
    Returns:
        String base64 contenant: salt + métadonnées chiffrées
    """
    import json
    
    # Générer un salt si non fourni
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    
    # Dériver la clé maître
    master_key = derive_master_key(user_password, salt)
    
    # Convertir en JSON et chiffrer
    json_data = json.dumps(metadata, ensure_ascii=False).encode('utf-8')
    f = Fernet(master_key)
    encrypted_data = f.encrypt(json_data)
    
    # Retourner salt + données chiffrées en base64
    combined = salt + encrypted_data
    return base64.b64encode(combined).decode('utf-8')


def decrypt_metadata(encrypted_metadata_data: str, user_password: str) -> dict:
    """
    Déchiffre les métadonnées sensibles
    
    Args:
        encrypted_metadata_data: String base64 contenant salt + métadonnées chiffrées
        user_password: Mot de passe utilisateur
        
    Returns:
        Dictionnaire contenant les métadonnées déchiffrées
        
    Raises:
        ValueError: Si le mot de passe est incorrect
    """
    import json
    
    try:
        # Décoder base64
        combined = base64.b64decode(encrypted_metadata_data.encode('utf-8'))
        
        # Extraire salt et données chiffrées
        salt = combined[:SALT_SIZE]
        encrypted_data = combined[SALT_SIZE:]
        
        # Dériver la clé maître
        master_key = derive_master_key(user_password, salt)
        
        # Déchiffrer
        f = Fernet(master_key)
        json_data = f.decrypt(encrypted_data)
        
        # Convertir JSON en dict
        return json.loads(json_data.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Impossible de déchiffrer les métadonnées. Mot de passe incorrect ou données corrompues: {str(e)}")


def calculate_integrity_hash(data: bytes) -> str:
    """
    Calcule un hash d'intégrité pour vérifier que les données n'ont pas été modifiées
    
    Args:
        data: Données à hasher
        
    Returns:
        Hash SHA-256 en hexadécimal
    """
    return hashlib.sha256(data).hexdigest()


def verify_integrity(data: bytes, expected_hash: str) -> bool:
    """
    Vérifie l'intégrité des données
    
    Args:
        data: Données à vérifier
        expected_hash: Hash attendu
        
    Returns:
        True si l'intégrité est vérifiée
        
    Raises:
        ValueError: Si l'intégrité n'est pas vérifiée (données corrompues ou modifiées)
    """
    calculated_hash = calculate_integrity_hash(data)
    if calculated_hash != expected_hash:
        raise ValueError(
            f"Intégrité des données compromise ! "
            f"Hash calculé: {calculated_hash[:16]}..., "
            f"Hash attendu: {expected_hash[:16]}..."
        )
    return True

