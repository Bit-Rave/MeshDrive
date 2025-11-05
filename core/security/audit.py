"""
Module de logging d'audit pour tracer les actions des utilisateurs
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from core.database import User


class AuditAction(str, Enum):
    """Types d'actions auditables"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER = "REGISTER"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    FILE_DELETE = "FILE_DELETE"
    FILE_MOVE = "FILE_MOVE"
    FOLDER_CREATE = "FOLDER_CREATE"
    FOLDER_DELETE = "FOLDER_DELETE"
    FOLDER_DOWNLOAD = "FOLDER_DOWNLOAD"
    ACCESS_DENIED = "ACCESS_DENIED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_TOKEN = "INVALID_TOKEN"
    PATH_TRAVERSAL_ATTEMPT = "PATH_TRAVERSAL_ATTEMPT"
    INVALID_FILENAME = "INVALID_FILENAME"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


# Configuration du logger d'audit
AUDIT_LOG_DIR = Path(__file__).parent.parent.parent / "data" / "logs"
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.log"

# Créer le logger d'audit
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Handler pour fichier (si pas déjà configuré)
if not audit_logger.handlers:
    file_handler = logging.FileHandler(AUDIT_LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Format de log structuré
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)
    
    # Ne pas propager vers le logger racine
    audit_logger.propagate = False


def log_action(
    user_id: Optional[int],
    action: AuditAction,
    resource: Optional[str] = None,
    success: bool = True,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Enregistre une action dans le log d'audit
    
    Args:
        user_id: ID de l'utilisateur (None si non authentifié)
        action: Type d'action
        resource: Ressource concernée (ex: file_id, folder_path)
        success: True si l'action a réussi, False sinon
        details: Détails supplémentaires
        ip_address: Adresse IP de l'utilisateur
    """
    # Construire le message de log
    parts = [
        f"User: {user_id if user_id else 'ANONYMOUS'}",
        f"Action: {action.value}",
        f"Success: {success}"
    ]
    
    if resource:
        parts.append(f"Resource: {resource}")
    
    if details:
        parts.append(f"Details: {details}")
    
    if ip_address:
        parts.append(f"IP: {ip_address}")
    
    message = " | ".join(parts)
    
    # Logger selon le niveau
    if success:
        audit_logger.info(message)
    else:
        audit_logger.warning(message)


def log_user_action(
    user: Optional[User],
    action: AuditAction,
    resource: Optional[str] = None,
    success: bool = True,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Enregistre une action d'utilisateur (helper qui extrait user_id)
    
    Args:
        user: Objet User (peut être None)
        action: Type d'action
        resource: Ressource concernée
        success: True si l'action a réussi
        details: Détails supplémentaires
        ip_address: Adresse IP de l'utilisateur
    """
    user_id = user.id if user else None
    log_action(user_id, action, resource, success, details, ip_address)


def get_client_ip(request) -> Optional[str]:
    """
    Extrait l'adresse IP du client depuis une requête FastAPI
    
    Args:
        request: Objet Request de FastAPI
        
    Returns:
        Adresse IP du client ou None
    """
    # Essayer différents headers pour obtenir l'IP réelle
    if request:
        # X-Forwarded-For (pour les reverse proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Prendre la première IP (le client original)
            return forwarded.split(",")[0].strip()
        
        # X-Real-IP (pour nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # IP directe du client
        if hasattr(request, 'client') and request.client:
            return request.client.host
    
    return None

