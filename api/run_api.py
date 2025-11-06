"""
Script pour lancer l'API FastAPI
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer cryptolib
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.crypto_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

