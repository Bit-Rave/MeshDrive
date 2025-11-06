"""
Script pour lancer l'API FastAPI
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer cryptolib
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
def main():
    uvicorn.run(
        "API.crypto_api:app",
        host="127.0.0.1",
        port=4040,
        reload=False,
        log_level="info"
    )