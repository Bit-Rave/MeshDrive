"""Fonctions utilitaires pour le système de chiffrement"""


def format_size(size_bytes: int) -> str:
    """
    Formate la taille en format lisible par l'humain
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Chaîne formatée (ex: "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

