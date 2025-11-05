"""Gestion des chunks (découpage et réassemblage)"""

import hashlib
import logging
from pathlib import Path
from typing import List, Dict
from .models import EncryptedChunk
from .config import CHUNK_SIZE, CHUNKS_DIR


logger = logging.getLogger(__name__)


class ChunkManager:
    """Gère le découpage et le réassemblage des fichiers en chunks"""
    
    def __init__(self, chunks_dir: Path = CHUNKS_DIR, chunk_size: int = CHUNK_SIZE):
        self.chunks_dir = chunks_dir
        self.chunk_size = chunk_size
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
    
    
    def split_into_chunks(self, data: bytes, file_id: str) -> List[EncryptedChunk]:
        """
        Découpe les données en chunks et les sauvegarde
        
        Args:
            data: Données à découper
            file_id: ID du fichier
            
        Returns:
            Liste des chunks créés
        """
        chunks = []
        total_size = len(data)
        num_chunks = (total_size + self.chunk_size - 1) // self.chunk_size
        
        logger.info(f"  ✂️  Découpage en {num_chunks} chunks...")
        
        for i in range(num_chunks):
            start = i * self.chunk_size
            end = min(start + self.chunk_size, total_size)
            chunk_data = data[start:end]
            
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            chunk_id = chunk_hash[:16]
            
            # Sauvegarde du chunk
            chunk_filename = f"{file_id}_chunk_{i:04d}.enc"
            chunk_path = self.chunks_dir / chunk_filename
            
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            
            chunk = EncryptedChunk(
                chunk_id=chunk_id,
                data=chunk_data,
                size=len(chunk_data),
                index=i,
                hash_sha256=chunk_hash,
                file_path=str(chunk_path)
            )
            
            chunks.append(chunk)
            logger.debug(f"    Chunk {i}: {chunk_id} → {chunk_filename}")
        
        logger.info(f"  ✅ {len(chunks)} chunks créés")
        return chunks
    
    
    def load_chunks_from_disk(self, chunks_metadata: List[Dict]) -> List[Dict]:
        """
        Charge les chunks depuis le disque
        
        Args:
            chunks_metadata: Métadonnées des chunks
            
        Returns:
            Liste de {'data': bytes, 'index': int}
        """
        chunks_data = []
        
        logger.info(f"  📥 Chargement de {len(chunks_metadata)} chunks...")
        
        for chunk_meta in chunks_metadata:
            chunk_path = Path(chunk_meta['file_path'])
            
            if not chunk_path.exists():
                raise FileNotFoundError(
                    f"❌ Chunk introuvable: {chunk_path}\n"
                    f"   Vérifiez que le fichier existe dans {self.chunks_dir}"
                )
            
            with open(chunk_path, 'rb') as f:
                chunk_data = f.read()
            
            # Vérification du hash
            actual_hash = hashlib.sha256(chunk_data).hexdigest()
            expected_hash = chunk_meta['hash']
            
            if actual_hash != expected_hash:
                raise ValueError(
                    f"❌ Chunk corrompu: {chunk_path.name}\n"
                    f"   Hash attendu: {expected_hash}\n"
                    f"   Hash reçu:    {actual_hash}"
                )
            
            chunks_data.append({
                'data': chunk_data,
                'index': chunk_meta['index']
            })
            
            logger.debug(f"    ✓ Chunk {chunk_meta['index']}: {chunk_path.name}")
        
        logger.info(f"  ✅ Tous les chunks chargés")
        return chunks_data
    
    
    def reassemble_chunks(self, chunks_data: List[Dict]) -> bytes:
        """
        Réassemble les chunks dans l'ordre
        
        Args:
            chunks_data: Liste des chunks à réassembler
            
        Returns:
            Données réassemblées
        """
        logger.info(f"  🔗 Réassemblage des chunks...")
        sorted_chunks = sorted(chunks_data, key=lambda c: c['index'])
        data = b''.join(c['data'] for c in sorted_chunks)
        logger.info(f"  ✅ Réassemblage terminé")
        return data
    
    
    def delete_chunks(self, chunks_metadata: List[Dict]):
        """Supprime les chunks du disque"""
        for chunk_meta in chunks_metadata:
            chunk_path = Path(chunk_meta['file_path'])
            if chunk_path.exists():
                chunk_path.unlink()
                logger.debug(f"    🗑️  {chunk_path.name}")
        
        logger.info(f"  ✅ {len(chunks_metadata)} chunks supprimés")
