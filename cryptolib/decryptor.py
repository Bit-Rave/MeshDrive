"""Module de déchiffrement"""

import hashlib
import logging
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .chunk_manager import ChunkManager
from .metadata_manager import MetadataManager


logger = logging.getLogger(__name__)


class Decryptor:
    """Gère le déchiffrement des fichiers"""
    
    def __init__(self, chunk_manager: ChunkManager, metadata_manager: MetadataManager):
        self.chunk_manager = chunk_manager
        self.metadata_manager = metadata_manager
    
    
    def decrypt_file(self, file_id: str, output_path: str = None) -> str:
        """
        Déchiffre un fichier et le sauvegarde

        Args:
            file_id: ID du fichier
            output_path: Chemin de sauvegarde (optionnel, sinon ./output/)

        Returns:
            Chemin du fichier déchiffré
        """
        logger.info(f"🔓 Déchiffrement: {file_id}")

        # 1. Chargement métadonnées
        metadata = self.metadata_manager.load_metadata(file_id)
        original_name = metadata['original_name']
        logger.info(f"  📄 Fichier: {original_name}")

        # 2. Récupération clé + nonce
        key = bytes.fromhex(metadata['encryption']['key'])
        nonce = bytes.fromhex(metadata['encryption']['nonce'])
        logger.info(f"  🔑 Clé chargée")

        # 3. Chargement des chunks
        chunks_data = self.chunk_manager.load_chunks_from_disk(metadata['chunks'])

        # 4. Réassemblage
        ciphertext = self.chunk_manager.reassemble_chunks(chunks_data)
        logger.info(f"  📦 Données réassemblées: {self._format_size(len(ciphertext))}")

        # 5. Vérification intégrité
        self._verify_integrity(ciphertext, file_id)
        logger.info(f"  ✅ Intégrité vérifiée")

        # 6. Déchiffrement
        plaintext = self._decrypt_data(ciphertext, key, nonce)
        logger.info(f"  ✅ Déchiffrement réussi: {self._format_size(len(plaintext))}")

        # 7. Sauvegarde sur disque
        if output_path is None:
            from pathlib import Path
            output_path = Path("./output") / original_name
        else:
            from pathlib import Path
            output_path = Path(output_path)

        # Créer le dossier parent si nécessaire
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Écrire le fichier
        with open(output_path, 'wb') as f:
            f.write(plaintext)

        logger.info(f"  💾 Sauvegardé: {output_path}")
        logger.info(f"✅ Déchiffrement terminé\n")

        return str(output_path)
    
    
    def _verify_integrity(self, data: bytes, expected_file_id: str):
        """Vérifie l'intégrité des données"""
        actual_file_id = hashlib.sha256(data).hexdigest()[:16]
        
        if actual_file_id != expected_file_id:
            raise ValueError(
                f"❌ CORRUPTION DÉTECTÉE!\n"
                f"   File ID attendu: {expected_file_id}\n"
                f"   File ID reçu:    {actual_file_id}"
            )
    
    
    def _decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Déchiffre les données"""
        aesgcm = AESGCM(key)
        
        try:
            return aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        except Exception as e:
            raise ValueError(
                f"❌ Déchiffrement échoué!\n"
                f"   Causes possibles:\n"
                f"   • Clé incorrecte\n"
                f"   • Données corrompues\n"
                f"   Erreur: {str(e)}"
            )
    
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formate la taille"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
