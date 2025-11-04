"""
API FastAPI pour exposer les fonctionnalités de cryptolib
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
import tempfile
import os
import logging
import zipfile

from cryptolib import CryptoSystem

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'API FastAPI
app = FastAPI(
    title="MeshDrive Crypto API",
    description="API pour chiffrer et déchiffrer des fichiers",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques du dossier web
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")

# Initialisation du système cryptographique
crypto_system = CryptoSystem()


# Modèles Pydantic pour les requêtes/réponses
class FileInfo(BaseModel):
    """Informations sur un fichier chiffré"""
    file_id: str
    original_name: str
    file_size: int
    chunk_count: int
    upload_date: str


class FileDetails(BaseModel):
    """Détails complets d'un fichier"""
    file_id: str
    name: str
    size: int
    encrypted_size: int
    algorithm: str
    chunks: int
    created_at: str


class EncryptResponse(BaseModel):
    """Réponse après chiffrement"""
    file_id: str
    original_name: str
    chunk_count: int
    folder_path: str
    message: str


class FolderInfo(BaseModel):
    """Informations sur un dossier"""
    folder_id: str
    folder_name: str
    folder_path: str
    parent_path: str
    created_at: str


class CreateFolderRequest(BaseModel):
    """Requête pour créer un dossier"""
    folder_name: str
    parent_path: str = "/"


class FolderContentsResponse(BaseModel):
    """Contenu d'un dossier"""
    folder_path: str
    files: List[FileInfo]
    folders: List[FolderInfo]


class MoveFileRequest(BaseModel):
    """Requête pour déplacer un fichier"""
    new_folder_path: str


class DecryptResponse(BaseModel):
    """Réponse après déchiffrement"""
    file_id: str
    original_name: str
    output_path: str
    message: str


# Endpoints

@app.post("/encrypt", response_model=EncryptResponse)
async def encrypt_file(file: UploadFile = File(...), folder_path: str = "/"):
    """
    Chiffre un fichier uploadé
    
    Args:
        file: Fichier à chiffrer (multipart/form-data)
        folder_path: Chemin du dossier de destination
    
    Returns:
        Informations sur le fichier chiffré
    """
    try:
        logger.info(f"🔐 Début du chiffrement: {file.filename}")
        
        # Sauvegarder temporairement le fichier uploadé
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            # Écrire le contenu du fichier uploadé
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Chiffrer le fichier avec le nom original
            result = crypto_system.encrypt_file(tmp_path, folder_path, file.filename)
            
            # Extraire les informations
            if hasattr(result, 'file_id'):
                file_id = result.file_id
                original_name = result.original_name
                chunk_count = len(result.chunks) if hasattr(result, 'chunks') else 0
                result_folder_path = getattr(result, 'folder_path', folder_path)
            else:
                file_id = result.get('file_id', '')
                original_name = result.get('original_name', file.filename)
                chunks = result.get('chunks', [])
                chunk_count = len(chunks)
                result_folder_path = result.get('folder_path', folder_path)
            
            logger.info(f"✅ Chiffrement réussi: {file_id}")
            
            return EncryptResponse(
                file_id=file_id,
                original_name=original_name,
                chunk_count=chunk_count,
                folder_path=result_folder_path,
                message="Fichier chiffré avec succès"
            )
            
        finally:
            # Supprimer le fichier temporaire
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"❌ Erreur lors du chiffrement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chiffrement: {str(e)}")


@app.get("/decrypt/{file_id}")
async def decrypt_file(file_id: str, download: bool = False):
    """
    Déchiffre un fichier
    
    Args:
        file_id: ID du fichier à déchiffrer
        download: Si True, télécharge le fichier. Si False, retourne le chemin
    
    Returns:
        Fichier déchiffré ou chemin du fichier
    """
    try:
        logger.info(f"🔓 Début du déchiffrement: {file_id}")
        
        # Obtenir les informations du fichier
        file_info = crypto_system.get_file_info(file_id)
        original_name = file_info.get('name', f"file_{file_id}")
        
        # Créer un fichier temporaire pour le déchiffrement
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(original_name).suffix) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Déchiffrer le fichier
            output_path = crypto_system.decrypt_file(file_id, tmp_path)
            
            logger.info(f"✅ Déchiffrement réussi: {output_path}")
            
            if download:
                # Retourner le fichier en téléchargement
                return FileResponse(
                    output_path,
                    filename=original_name,
                    media_type='application/octet-stream'
                )
            else:
                # Retourner le chemin
                return DecryptResponse(
                    file_id=file_id,
                    original_name=original_name,
                    output_path=output_path,
                    message="Fichier déchiffré avec succès"
                )
        except Exception as decrypt_error:
            # Nettoyer le fichier temporaire en cas d'erreur
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise decrypt_error
            
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du déchiffrement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du déchiffrement: {str(e)}")


@app.get("/files", response_model=List[FileInfo])
async def list_files(folder_path: str = "/"):
    """
    Liste tous les fichiers chiffrés dans un dossier
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
    
    Returns:
        Liste des fichiers avec leurs informations
    """
    try:
        files = crypto_system.list_files(folder_path)
        logger.info(f"📋 Liste de {len(files)} fichiers dans {folder_path}")
        return files
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de la liste: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/files/{file_id}", response_model=FileDetails)
async def get_file_info(file_id: str):
    """
    Récupère les informations détaillées d'un fichier
    
    Args:
        file_id: ID du fichier
    
    Returns:
        Détails du fichier
    """
    try:
        file_info = crypto_system.get_file_info(file_id)
        logger.info(f"📄 Informations du fichier: {file_id}")
        return file_info
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.put("/files/{file_id}/move")
async def move_file(file_id: str, request: MoveFileRequest):
    """
    Déplace un fichier vers un nouveau dossier
    
    Args:
        file_id: ID du fichier à déplacer
        request: Requête contenant le nouveau chemin du dossier
    
    Returns:
        Message de confirmation
    """
    try:
        logger.info(f"📦 Déplacement du fichier {file_id} vers {request.new_folder_path}")
        
        # Déplacer le fichier
        crypto_system.move_file(file_id, request.new_folder_path)
        
        logger.info(f"✅ Fichier déplacé avec succès: {file_id}")
        
        return {
            "message": "Fichier déplacé avec succès",
            "file_id": file_id,
            "new_folder_path": request.new_folder_path
        }
    except ValueError as e:
        logger.error(f"❌ Erreur lors du déplacement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du déplacement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du déplacement: {str(e)}")


@app.delete("/files/{file_id}")
async def delete_file(file_id: str, delete_chunks: bool = True):
    """
    Supprime un fichier chiffré
    
    Args:
        file_id: ID du fichier à supprimer
        delete_chunks: Si True, supprime aussi les chunks sur le disque
    
    Returns:
        Message de confirmation
    """
    try:
        # Vérifier que le fichier existe
        crypto_system.get_file_info(file_id)
        
        # Supprimer le fichier
        crypto_system.delete_file(file_id, delete_chunks=delete_chunks)
        
        logger.info(f"🗑️  Fichier supprimé: {file_id}")
        
        return {
            "message": "Fichier supprimé avec succès",
            "file_id": file_id
        }
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_id}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "MeshDrive Crypto API",
        "version": "1.0.0",
        "endpoints": {
            "encrypt": "POST /encrypt - Chiffrer un fichier",
            "decrypt": "GET /decrypt/{file_id}?download=true - Déchiffrer un fichier",
            "list_files": "GET /files - Lister tous les fichiers",
            "get_file_info": "GET /files/{file_id} - Obtenir les infos d'un fichier",
            "delete_file": "DELETE /files/{file_id} - Supprimer un fichier"
        },
        "web_interface": "http://localhost:8000/web/"
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "service": "MeshDrive Crypto API"}


# Endpoints pour les dossiers

@app.post("/folders", response_model=FolderInfo)
async def create_folder(request: CreateFolderRequest):
    """
    Crée un nouveau dossier
    
    Args:
        request: Requête contenant le nom du dossier et le chemin parent
    
    Returns:
        Informations sur le dossier créé
    """
    try:
        logger.info(f"📁 Création du dossier: {request.folder_name} dans {request.parent_path}")
        
        folder = crypto_system.create_folder(request.folder_name, request.parent_path)
        
        logger.info(f"✅ Dossier créé: {folder.folder_path}")
        
        return {
            'folder_id': folder.folder_id,
            'folder_name': folder.folder_name,
            'folder_path': folder.folder_path,
            'parent_path': folder.parent_path,
            'created_at': folder.created_at
        }
    except ValueError as e:
        logger.error(f"❌ Erreur lors de la création du dossier: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du dossier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@app.get("/folders", response_model=List[FolderInfo])
async def list_folders(parent_path: str = "/"):
    """
    Liste tous les dossiers dans un dossier parent
    
    Args:
        parent_path: Chemin du dossier parent (par défaut "/" pour la racine)
    
    Returns:
        Liste des dossiers
    """
    try:
        folders = crypto_system.list_folders(parent_path)
        logger.info(f"📁 Liste de {len(folders)} dossiers dans {parent_path}")
        return folders
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des dossiers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/folders-all", response_model=List[FolderInfo])
async def list_all_folders():
    """
    Liste tous les dossiers du système
    
    Returns:
        Liste de tous les dossiers
    """
    try:
        all_folders_raw = crypto_system.list_all_folders()
        # S'assurer que tous les champs sont présents et valides
        all_folders = []
        for folder in all_folders_raw:
            # Vérifier que tous les champs requis sont présents
            if all(key in folder for key in ['folder_id', 'folder_name', 'folder_path', 'parent_path', 'created_at']):
                all_folders.append({
                    'folder_id': str(folder['folder_id']),
                    'folder_name': str(folder['folder_name']),
                    'folder_path': str(folder['folder_path']),
                    'parent_path': str(folder['parent_path']),
                    'created_at': str(folder['created_at'])
                })
        logger.info(f"📁 Liste de {len(all_folders)} dossiers au total")
        return all_folders
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de tous les dossiers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/folders/{folder_path:path}", response_model=FolderInfo)
async def get_folder(folder_path: str):
    """
    Récupère les métadonnées d'un dossier
    
    Args:
        folder_path: Chemin du dossier
    
    Returns:
        Informations sur le dossier
    """
    try:
        folder = crypto_system.get_folder(folder_path)
        if not folder:
            raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
        
        logger.info(f"📁 Informations du dossier: {folder_path}")
        return folder
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.delete("/folders/{folder_path:path}")
async def delete_folder(folder_path: str, recursive: bool = False):
    """
    Supprime un dossier
    
    Args:
        folder_path: Chemin du dossier à supprimer
        recursive: Si True, supprime aussi les sous-dossiers et fichiers
    
    Returns:
        Message de confirmation
    """
    try:
        # Vérifier que le dossier existe
        folder = crypto_system.get_folder(folder_path)
        if not folder:
            raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
        
        # Supprimer le dossier
        success = crypto_system.delete_folder(folder_path, recursive=recursive)
        
        if not success:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
        
        logger.info(f"🗑️  Dossier supprimé: {folder_path}")
        
        return {
            "message": "Dossier supprimé avec succès",
            "folder_path": folder_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@app.get("/folder-contents", response_model=FolderContentsResponse)
async def get_folder_contents(folder_path: str = "/"):
    """
    Récupère le contenu d'un dossier (fichiers et sous-dossiers)
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
    
    Returns:
        Contenu du dossier (fichiers et dossiers)
    """
    try:
        contents = crypto_system.get_folder_contents(folder_path)
        logger.info(f"📁 Contenu du dossier {folder_path}: {len(contents['files'])} fichiers, {len(contents['folders'])} dossiers")
        return {
            'folder_path': folder_path,
            'files': contents['files'],
            'folders': contents['folders']
        }
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du contenu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/download-folder/{folder_path:path}")
async def download_folder_as_zip(folder_path: str):
    """
    Télécharge un dossier complet en ZIP
    
    Args:
        folder_path: Chemin du dossier à télécharger (peut être "/" pour la racine)
    
    Returns:
        Fichier ZIP contenant le dossier
    """
    try:
        logger.info(f"📦 Téléchargement du dossier en ZIP: {folder_path}")
        
        # Pour la racine, on télécharge directement sans vérifier l'existence
        if folder_path != "/":
            # Vérifier que le dossier existe
            folder = crypto_system.get_folder(folder_path)
            if not folder:
                raise HTTPException(status_code=404, detail=f"Dossier introuvable: {folder_path}")
            folder_name = folder['folder_name']
        else:
            folder_name = "root"
        
        # Créer un fichier ZIP temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            zip_path = tmp_zip.name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Fonction récursive pour ajouter les fichiers et dossiers
                def add_folder_to_zip(folder_path_inner, zip_path_inner, base_path=""):
                    contents = crypto_system.get_folder_contents(folder_path_inner)
                    
                    # Ajouter les fichiers
                    for file_info in contents['files']:
                        try:
                            # Déchiffrer le fichier temporairement
                            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                output_path = tmp_file.name
                            
                            crypto_system.decrypt_file(file_info['file_id'], output_path)
                            
                            # Ajouter au ZIP avec le chemin relatif
                            if base_path:
                                zip_path_inner.write(output_path, f"{base_path}/{file_info['original_name']}")
                            else:
                                zip_path_inner.write(output_path, file_info['original_name'])
                            
                            # Supprimer le fichier temporaire
                            if os.path.exists(output_path):
                                os.unlink(output_path)
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur lors du téléchargement du fichier {file_info['original_name']}: {str(e)}")
                            continue
                    
                    # Ajouter les sous-dossiers récursivement
                    for subfolder in contents['folders']:
                        subfolder_base = f"{base_path}/{subfolder['folder_name']}" if base_path else subfolder['folder_name']
                        add_folder_to_zip(subfolder['folder_path'], zip_path_inner, subfolder_base)
                
                # Ajouter le contenu du dossier
                add_folder_to_zip(folder_path, zipf, "")
            
            # Retourner le fichier ZIP
            return FileResponse(
                zip_path,
                filename=f"{folder_name}.zip",
                media_type='application/zip'
            )
        except Exception as e:
            # Nettoyer le fichier ZIP en cas d'erreur
            if os.path.exists(zip_path):
                os.unlink(zip_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors du téléchargement du dossier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")


@app.post("/encrypt-folder")
async def encrypt_folder(folder_path: str = "/", files: List[UploadFile] = File(...)):
    """
    Chiffre plusieurs fichiers (upload de dossier)
    
    Args:
        folder_path: Chemin du dossier de destination
        files: Liste des fichiers à uploader (multipart/form-data)
    
    Returns:
        Liste des fichiers chiffrés
    """
    try:
        logger.info(f"📁 Upload de {len(files)} fichiers dans {folder_path}")
        
        results = []
        errors = []
        
        for file in files:
            try:
                # Sauvegarder temporairement le fichier
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                try:
                    # Chiffrer le fichier avec le nom original
                    result = crypto_system.encrypt_file(tmp_path, folder_path, file.filename)
                    
                    # Extraire les informations
                    if hasattr(result, 'file_id'):
                        file_id = result.file_id
                        original_name = result.original_name
                    else:
                        file_id = result.get('file_id', '')
                        original_name = result.get('original_name', file.filename)
                    
                    results.append({
                        'file_id': file_id,
                        'original_name': original_name,
                        'folder_path': folder_path
                    })
                finally:
                    # Supprimer le fichier temporaire
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du chiffrement de {file.filename}: {str(e)}")
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return {
            'success': len(results),
            'errors': len(errors),
            'files': results,
            'error_details': errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload du dossier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

