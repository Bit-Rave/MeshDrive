"""
API FastAPI pour exposer les fonctionnalités de cryptolib
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import tempfile
import os
import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from cryptolib import CryptoSystem
from cryptolib.models import (
    FileInfo, FileDetails, EncryptResponse, FolderInfo,
    CreateFolderRequest, FolderContentsResponse, MoveFileRequest, DecryptResponse
)

# Import des modules d'authentification
from core.database import init_db, get_db, User
from core.auth_routes import router as auth_router
from core.auth import (
    get_current_active_user,
    SECRET_KEY,
    ALGORITHM,
    TokenData,
    get_user_by_username
)
from core.utils import get_crypto_system_for_user, check_quota, update_user_quota
from jose import JWTError, jwt

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de la base de données
init_db()

# Initialisation de l'API FastAPI
app = FastAPI(
    title="MeshDrive Crypto API",
    description="API pour chiffrer et déchiffrer des fichiers",
    version="2.0.0"
)

# Inclure les routes d'authentification
app.include_router(auth_router)

# Configuration CORS pour permettre les requêtes depuis le web
# Avec allow_credentials=True, on ne peut pas utiliser allow_origins=["*"]
# Il faut spécifier les origines exactes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "authorization", "Content-Type", "content-type"],
)

# Servir les fichiers statiques du dossier web
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    # Servir les fichiers statiques (JS, CSS, etc.) sur /static
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    
    # Dashboard à la racine
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Point d'entrée principal - Dashboard"""
        dashboard_path = web_dir / "dashboard.html"
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return f.read()
        return {"message": "MeshDrive Crypto API", "version": "2.0.0"}
    
    # Page de login
    @app.get("/login.html", response_class=HTMLResponse)
    async def login_page():
        """Page de connexion/inscription"""
        login_path = web_dir / "login.html"
        if login_path.exists():
            with open(login_path, 'r', encoding='utf-8') as f:
                return f.read()
        return {"message": "Page de login non trouvée"}
    
    # Drive sur /drive
    @app.get("/drive", response_class=HTMLResponse)
    async def drive():
        """Interface web MeshDrive - Drive"""
        drive_path = web_dir / "drive.html"
        if drive_path.exists():
            with open(drive_path, 'r', encoding='utf-8') as f:
                return f.read()
        return {"message": "MeshDrive Crypto API", "version": "2.0.0"}

# Import des utilitaires déjà fait en haut


# Endpoints

@app.post("/encrypt", response_model=EncryptResponse)
@app.post("/api/encrypt", response_model=EncryptResponse)  # Alias pour compatibilité
async def encrypt_file(
    file: UploadFile = File(...),
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user)
):
    """
    Chiffre un fichier uploadé
    
    Args:
        file: Fichier à chiffrer (multipart/form-data)
        folder_path: Chemin du dossier de destination
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Informations sur le fichier chiffré
    """
    try:
        logger.info(f"🔐 Début du chiffrement: {file.filename} (user: {current_user.id})")
        
        # Sauvegarder temporairement le fichier uploadé pour obtenir sa taille
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            # Écrire le contenu du fichier uploadé
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
            file_size = len(content)
        
        # Vérifier le quota avant le chiffrement
        if not check_quota(current_user, file_size):
            # Nettoyer le fichier temporaire
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise HTTPException(
                status_code=403,
                detail=f"Quota de stockage dépassé. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Fichier: {file_size} bytes"
            )
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
            
            # Mettre à jour le quota de l'utilisateur
            db = next(get_db())
            try:
                update_user_quota(db, current_user.id, file_size, is_upload=True)
                logger.info(f"📊 Quota mis à jour: {current_user.used_bytes + file_size}/{current_user.quota_bytes} bytes")
            finally:
                db.close()
            
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
@app.get("/api/decrypt/{file_id}")  # Alias pour compatibilité
async def decrypt_file(
    file_id: str,
    download: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Déchiffre un fichier
    
    Args:
        file_id: ID du fichier à déchiffrer
        download: Si True, télécharge le fichier. Si False, retourne le chemin
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Fichier déchiffré ou chemin du fichier
    """
    try:
        logger.info(f"🔓 Début du déchiffrement: {file_id} (user: {current_user.id})")
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
@app.get("/api/files", response_model=List[FileInfo])  # Alias pour compatibilité
async def list_files(
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user)
):
    """
    Liste tous les fichiers chiffrés dans un dossier
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Liste des fichiers avec leurs informations
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        files = crypto_system.list_files(folder_path)
        logger.info(f"📋 Liste de {len(files)} fichiers dans {folder_path}")
        return files
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de la liste: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/files/{file_id}", response_model=FileDetails)
@app.get("/api/files/{file_id}", response_model=FileDetails)  # Alias pour compatibilité
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les informations détaillées d'un fichier
    
    Args:
        file_id: ID du fichier
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Détails du fichier
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
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
@app.put("/api/files/{file_id}/move")  # Alias pour compatibilité
async def move_file(
    file_id: str,
    request: MoveFileRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Déplace un fichier vers un nouveau dossier
    
    Args:
        file_id: ID du fichier à déplacer
        request: Requête contenant le nouveau chemin du dossier
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Message de confirmation
    """
    try:
        logger.info(f"📦 Déplacement du fichier {file_id} vers {request.new_folder_path} (user: {current_user.id})")
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
@app.delete("/api/files/{file_id}")  # Alias pour compatibilité
async def delete_file(
    file_id: str,
    delete_chunks: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un fichier chiffré
    
    Args:
        file_id: ID du fichier à supprimer
        delete_chunks: Si True, supprime aussi les chunks sur le disque
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Message de confirmation
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
        # Vérifier que le fichier existe et obtenir sa taille
        file_info = crypto_system.get_file_info(file_id)
        file_size = file_info.get('size', 0)
        
        # Supprimer le fichier
        crypto_system.delete_file(file_id, delete_chunks=delete_chunks)
        
        # Mettre à jour le quota de l'utilisateur (diminuer)
        if file_size > 0:
            db = next(get_db())
            try:
                update_user_quota(db, current_user.id, file_size, is_upload=False)
                logger.info(f"📊 Quota mis à jour: -{file_size} bytes")
            finally:
                db.close()
        
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


@app.get("/api")
async def api_info():
    """Informations sur l'API"""
    return {
        "message": "MeshDrive Crypto API",
        "version": "1.0.0",
        "endpoints": {
            "encrypt": "POST /encrypt - Chiffrer un fichier",
            "decrypt": "GET /decrypt/{file_id}?download=true - Déchiffrer un fichier",
            "list_files": "GET /files - Lister tous les fichiers",
            "get_file_info": "GET /files/{file_id} - Obtenir les infos d'un fichier",
            "delete_file": "DELETE /files/{file_id} - Supprimer un fichier"
        }
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "service": "MeshDrive Crypto API"}


# Endpoints pour les dossiers

@app.post("/folders", response_model=FolderInfo)
@app.post("/api/folders", response_model=FolderInfo)  # Alias pour compatibilité
async def create_folder(
    request: CreateFolderRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un nouveau dossier
    
    Args:
        request: Requête contenant le nom du dossier et le chemin parent
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Informations sur le dossier créé
    """
    try:
        logger.info(f"📁 Création du dossier: {request.folder_name} dans {request.parent_path} (user: {current_user.id})")
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
@app.get("/api/folders", response_model=List[FolderInfo])  # Alias pour compatibilité
async def list_folders(
    parent_path: str = "/",
    current_user: User = Depends(get_current_active_user)
):
    """
    Liste tous les dossiers dans un dossier parent
    
    Args:
        parent_path: Chemin du dossier parent (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Liste des dossiers
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        folders = crypto_system.list_folders(parent_path)
        logger.info(f"📁 Liste de {len(folders)} dossiers dans {parent_path}")
        return folders
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des dossiers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@app.get("/folders-all", response_model=List[FolderInfo])
@app.get("/api/folders-all", response_model=List[FolderInfo])  # Alias pour compatibilité
async def list_all_folders(
    current_user: User = Depends(get_current_active_user)
):
    """
    Liste tous les dossiers du système
    
    Args:
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Liste de tous les dossiers
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
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
@app.get("/api/folders/{folder_path:path}", response_model=FolderInfo)  # Alias pour compatibilité
async def get_folder(
    folder_path: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les métadonnées d'un dossier
    
    Args:
        folder_path: Chemin du dossier
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Informations sur le dossier
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
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
@app.delete("/api/folders/{folder_path:path}")  # Alias pour compatibilité
async def delete_folder(
    folder_path: str,
    recursive: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un dossier
    
    Args:
        folder_path: Chemin du dossier à supprimer
        recursive: Si True, supprime aussi les sous-dossiers et fichiers
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Message de confirmation
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
@app.get("/api/folder-contents", response_model=FolderContentsResponse)  # Alias pour compatibilité avec le nouveau système
async def get_folder_contents(
    folder_path: str = "/",
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère le contenu d'un dossier (fichiers et sous-dossiers)
    
    Args:
        folder_path: Chemin du dossier (par défaut "/" pour la racine)
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Contenu du dossier (fichiers et dossiers)
    """
    try:
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
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


def _decrypt_file_for_zip(file_data: dict, crypto_system: CryptoSystem) -> dict:
    """Fonction helper pour déchiffrer un fichier dans un thread pour le ZIP"""
    try:
        file_id = file_data['file_id']
        zip_path_in_zip = file_data['zip_path']
        original_name = file_data['original_name']
        
        # Déchiffrer le fichier temporairement
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


@app.get("/download-folder/{folder_path:path}")
@app.get("/api/download-folder/{folder_path:path}")  # Alias pour compatibilité
async def download_folder_as_zip(
    folder_path: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Télécharge un dossier complet en ZIP avec multithreading pour le déchiffrement
    
    Args:
        folder_path: Chemin du dossier à télécharger (peut être "/" pour la racine)
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        Fichier ZIP contenant le dossier
    """
    try:
        logger.info(f"📦 Téléchargement du dossier en ZIP: {folder_path} (multithreading) (user: {current_user.id})")
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
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
            # Collecter tous les fichiers à déchiffrer
            all_files = []
            
            def collect_files(folder_path_inner, base_path=""):
                """Collecte récursivement tous les fichiers du dossier"""
                contents = crypto_system.get_folder_contents(folder_path_inner)
                
                # Ajouter les fichiers
                for file_info in contents['files']:
                    zip_path_in_zip = f"{base_path}/{file_info['original_name']}" if base_path else file_info['original_name']
                    all_files.append({
                        'file_id': file_info['file_id'],
                        'original_name': file_info['original_name'],
                        'zip_path': zip_path_in_zip
                    })
                
                # Ajouter les sous-dossiers récursivement
                for subfolder in contents['folders']:
                    subfolder_base = f"{base_path}/{subfolder['folder_name']}" if base_path else subfolder['folder_name']
                    collect_files(subfolder['folder_path'], subfolder_base)
            
            # Collecter tous les fichiers
            collect_files(folder_path, "")
            
            logger.info(f"  📄 {len(all_files)} fichiers à déchiffrer en parallèle")
            
            # Déchiffrer les fichiers en parallèle
            decrypted_files = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(_decrypt_file_for_zip, file_data, crypto_system) for file_data in all_files]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result['success']:
                            decrypted_files.append(result)
                        else:
                            logger.warning(f"⚠️ Erreur lors du déchiffrement de {result['original_name']}: {result['error']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur dans le thread: {str(e)}")
            
            # Ajouter les fichiers déchiffrés au ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for decrypted_file in decrypted_files:
                    try:
                        zipf.write(decrypted_file['output_path'], decrypted_file['zip_path'])
                        # Supprimer le fichier temporaire
                        if os.path.exists(decrypted_file['output_path']):
                            os.unlink(decrypted_file['output_path'])
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur lors de l'ajout au ZIP: {str(e)}")
                        # Nettoyer le fichier temporaire en cas d'erreur
                        if os.path.exists(decrypted_file['output_path']):
                            os.unlink(decrypted_file['output_path'])
            
            logger.info(f"  ✅ ZIP créé avec {len(decrypted_files)} fichiers")
            
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


def _encrypt_single_file(file_data: dict, crypto_system: CryptoSystem) -> dict:
    """Fonction helper pour chiffrer un fichier dans un thread"""
    try:
        file = file_data['file']
        folder_path = file_data['folder_path']
        tmp_path = file_data['tmp_path']
        
        # Chiffrer le fichier avec le nom original
        result = crypto_system.encrypt_file(tmp_path, folder_path, file.filename)
        
        # Extraire les informations
        if hasattr(result, 'file_id'):
            file_id = result.file_id
            original_name = result.original_name
        else:
            file_id = result.get('file_id', '')
            original_name = result.get('original_name', file.filename)
        
        return {
            'success': True,
            'file_id': file_id,
            'original_name': original_name,
            'folder_path': folder_path,
            'filename': file.filename
        }
    except Exception as e:
        return {
            'success': False,
            'filename': file_data['file'].filename,
            'error': str(e)
        }
    finally:
        # Supprimer le fichier temporaire
        if os.path.exists(file_data['tmp_path']):
            os.unlink(file_data['tmp_path'])


@app.post("/encrypt-folder")
@app.post("/api/encrypt-folder")  # Alias pour compatibilité (optionnel, car le frontend utilise /encrypt-folder)
async def encrypt_folder(
    request: Request,
    folder_path: str = "/",
    files: List[UploadFile] = File(...),
    token: Optional[str] = Form(None)
):
    """
    Chiffre plusieurs fichiers (upload de dossier) avec multithreading
    
    Args:
        request: Objet Request pour accéder aux headers et FormData
        folder_path: Chemin du dossier de destination
        files: Liste des fichiers à uploader (multipart/form-data)
        token: Token JWT depuis FormData (si le header Authorization est bloqué)
    
    Returns:
        Liste des fichiers chiffrés
    """
    # Authentifier l'utilisateur depuis le token (header ou FormData)
    
    # Récupérer le token depuis le header Authorization
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    final_token = None
    
    logger.info(f"🔑 Tentative d'authentification - Header: {auth_header is not None}")
    
    # Essayer d'abord depuis le header Authorization
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            final_token = parts[1]
            logger.info(f"✅ Token extrait depuis header Authorization")
    
    # Si pas de token dans le header, essayer depuis FormData (paramètre Form)
    if not final_token:
        if token:
            final_token = token
            logger.info(f"✅ Token extrait depuis FormData (paramètre Form)")
        else:
            # Essayer de lire FormData manuellement (fallback)
            try:
                form_data = await request.form()
                token_from_form = form_data.get("token")
                if token_from_form:
                    final_token = token_from_form
                    logger.info(f"✅ Token extrait depuis FormData (méthode manuelle)")
                else:
                    logger.warning(f"⚠️ Token non trouvé dans FormData. Champs disponibles: {list(form_data.keys())}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de lire FormData: {str(e)}")
    
    if not final_token:
        logger.error("❌ Token manquant - Authorization header: {}, FormData token (paramètre): {}".format(auth_header, token is not None))
        logger.error("Headers reçus: {}".format(list(request.headers.keys())))
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni dans la requête"
        )
    
    # Valider le token et obtenir l'utilisateur
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"Erreur JWT: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    db = next(get_db())
    try:
        user = get_user_by_username(db, username=token_data.username)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        current_user = user
    finally:
        db.close()
    
    try:
        # Log des headers pour debug
        logger.info(f"📁 Upload de {len(files)} fichiers dans {folder_path} (multithreading) (user: {current_user.id})")
        logger.info(f"🔑 Token reçu depuis: {'Header' if auth_header else 'FormData'}")
        
        # Obtenir le système cryptographique pour cet utilisateur
        crypto_system = get_crypto_system_for_user(current_user)
        
        # Préparer les fichiers pour le traitement parallèle et vérifier les quotas
        file_tasks = []
        total_size = 0
        file_sizes = {}
        
        for file in files:
            try:
                # Sauvegarder temporairement le fichier pour obtenir sa taille
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                    file_size = len(content)
                    file_sizes[file.filename] = file_size
                    total_size += file_size
                
                # Vérifier le quota pour chaque fichier
                if not check_quota(current_user, file_size):
                    # Nettoyer les fichiers temporaires déjà créés
                    for task in file_tasks:
                        if os.path.exists(task['tmp_path']):
                            os.unlink(task['tmp_path'])
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise HTTPException(
                        status_code=403,
                        detail=f"Quota de stockage dépassé pour {file.filename}. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Fichier: {file_size} bytes"
                    )
                
                file_tasks.append({
                    'file': file,
                    'folder_path': folder_path,
                    'tmp_path': tmp_path,
                    'file_size': file_size
                })
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Erreur lors de la préparation de {file.filename}: {str(e)}")
        
        # Vérifier le quota total
        if not check_quota(current_user, total_size):
            # Nettoyer les fichiers temporaires
            for task in file_tasks:
                if os.path.exists(task['tmp_path']):
                    os.unlink(task['tmp_path'])
            raise HTTPException(
                status_code=403,
                detail=f"Quota de stockage insuffisant pour tous les fichiers. Utilisé: {current_user.used_bytes}/{current_user.quota_bytes} bytes. Total requis: {total_size} bytes"
            )
        
        # Traiter les fichiers en parallèle avec ThreadPoolExecutor
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_encrypt_single_file, task, crypto_system) for task in file_tasks]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        results.append({
                            'file_id': result['file_id'],
                            'original_name': result['original_name'],
                            'folder_path': result['folder_path']
                        })
                        # Mettre à jour le quota pour ce fichier
                        if result['filename'] in file_sizes:
                            file_size = file_sizes[result['filename']]
                            db = next(get_db())
                            try:
                                update_user_quota(db, current_user.id, file_size, is_upload=True)
                                logger.info(f"📊 Quota mis à jour pour {result['filename']}: +{file_size} bytes")
                            finally:
                                db.close()
                    else:
                        errors.append({
                            'filename': result['filename'],
                            'error': result['error']
                        })
                        logger.error(f"❌ Erreur lors du chiffrement de {result['filename']}: {result['error']}")
                except Exception as e:
                    logger.error(f"❌ Erreur dans le thread: {str(e)}")
                    errors.append({
                        'filename': 'unknown',
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

