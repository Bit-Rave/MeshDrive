"""
Routes pour servir les fichiers statiques (HTML, CSS, JS)
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["static"])

# Chemin vers le dossier web
web_dir = Path(__file__).parent.parent.parent / "web"


@router.get("/", response_class=HTMLResponse)
async def root():
    """Point d'entrée principal - Dashboard"""
    dashboard_path = web_dir / "dashboard.html"
    if dashboard_path.exists():
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return f.read()
    return {"message": "MeshDrive Crypto API", "version": "2.0.0"}


@router.get("/login.html", response_class=HTMLResponse)
async def login_page():
    """Page de connexion/inscription"""
    login_path = web_dir / "login.html"
    if login_path.exists():
        with open(login_path, 'r', encoding='utf-8') as f:
            return f.read()
    return {"message": "Page de login non trouvée"}


@router.get("/drive", response_class=HTMLResponse)
async def drive():
    """Interface web MeshDrive - Drive"""
    drive_path = web_dir / "drive.html"
    if drive_path.exists():
        with open(drive_path, 'r', encoding='utf-8') as f:
            return f.read()
    return {"message": "Page drive non trouvée"}

