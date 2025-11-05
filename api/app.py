"""
API FastAPI principale - Point d'entrée de l'application
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from core.auth_routes import router as auth_router
from api.routes import files_router, folders_router, static_router
from api.routes.multipart_files import router as multipart_files_router

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

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "authorization", "Content-Type", "content-type"],
)

# Servir les fichiers statiques
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Inclure les routes
app.include_router(auth_router)
app.include_router(static_router)
app.include_router(files_router, prefix="/api")
app.include_router(folders_router, prefix="/api")
app.include_router(multipart_files_router)


# Routes de santé et info
@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "service": "MeshDrive Crypto API"}


@app.get("/api")
async def api_info():
    """Informations sur l'API"""
    return {
        "message": "MeshDrive Crypto API",
        "version": "2.0.0",
        "endpoints": {
            "encrypt": "POST /api/encrypt - Chiffrer un fichier",
            "decrypt": "GET /api/decrypt/{file_id}?download=true - Déchiffrer un fichier",
            "list_files": "GET /api/files - Lister tous les fichiers",
            "get_file_info": "GET /api/files/{file_id} - Obtenir les infos d'un fichier",
            "delete_file": "DELETE /api/files/{file_id} - Supprimer un fichier"
        }
    }

