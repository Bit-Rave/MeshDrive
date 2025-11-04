from .chunk_manager import ChunkManager
from .metadata_manager import MetadataManager
from .encryptor import Encryptor
from .decryptor import Decryptor
from .config import KEYS_DIR, CHUNKS_DIR, CHUNK_SIZE

class CryptoSystem:
    """Point d'entrée principal pour le chiffrement/déchiffrement"""

    def __init__(self, keys_dir=None, chunks_dir=None, chunk_size=None):
        keys_dir = keys_dir or KEYS_DIR
        chunks_dir = chunks_dir or CHUNKS_DIR
        chunk_size = chunk_size or CHUNK_SIZE

        self.chunk_manager = ChunkManager(chunks_dir, chunk_size)
        self.metadata_manager = MetadataManager(keys_dir)
        self.encryptor = Encryptor(self.chunk_manager, self.metadata_manager)
        self.decryptor = Decryptor(self.chunk_manager, self.metadata_manager)

    def encrypt_file(self, file_path: str):
        return self.encryptor.encrypt_file(file_path)

    def decrypt_file(self, file_id: str, output_path: str = None):
        return self.decryptor.decrypt_file(file_id, output_path)

    def list_files(self):
        return self.metadata_manager.list_files()

    def get_file_info(self, file_id: str):
        return self.metadata_manager.get_file_info(file_id)

    def delete_file(self, file_id: str, delete_chunks: bool = True):
        if delete_chunks:
            metadata = self.metadata_manager.load_metadata(file_id)
            self.chunk_manager.delete_chunks(metadata['chunks'])
        self.metadata_manager.delete_metadata(file_id)
