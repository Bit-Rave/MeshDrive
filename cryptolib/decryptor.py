import hashlib
import logging
from pathlib import Path
from typing import List, Dict
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
        logger.info(f"Déchiffrement: {file_id}")

        metadata = self.metadata_manager.load_metadata(file_id)
        original_name = metadata['original_name']

        key = bytes.fromhex(metadata['encryption']['key'])
        nonce = bytes.fromhex(metadata['encryption']['nonce'])

        # Chargement des chunks
        chunks_data = self.chunk_manager.load_chunks_from_disk(metadata['chunks'])

        # Réassemblage
        ciphertext = self.chunk_manager.reassemble_chunks(chunks_data)

        # Vérification intégrité
        self._verify_integrity(ciphertext, file_id)

        # Déchiffrement
        plaintext = self._decrypt_data(ciphertext, key, nonce)

        if output_path is None:
            output_path = Path("./output") / original_name
        else:
            output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(plaintext)

        return str(output_path)

    def _verify_integrity(self, data: bytes, expected_file_id: str):
        actual_file_id = hashlib.sha256(data).hexdigest()[:16]
        if actual_file_id != expected_file_id:
            raise ValueError("CORRUPTION DÉTECTÉE")

    def _decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, associated_data=None)
