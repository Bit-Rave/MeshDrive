# API FastAPI pour MeshDrive Crypto

Cette API expose les fonctionnalités de la bibliothèque `cryptolib` via des endpoints REST.

## Installation

Assurez-vous d'avoir installé les dépendances:
```bash
pip install fastapi uvicorn python-multipart
```

## Lancement de l'API

```bash
cd api
python run_api.py
```

Ou directement avec uvicorn:
```bash
cd api
uvicorn crypto_api:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible à l'adresse: `http://localhost:8000`

## Documentation interactive

Une fois l'API lancée, accédez à:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints disponibles

### 1. Chiffrer un fichier
**POST** `/encrypt`

Upload un fichier pour le chiffrer.

**Request:**
- Type: `multipart/form-data`
- Body: Fichier à uploader

**Response:**
```json
{
  "file_id": "1caeb429419db709",
  "original_name": "mon_fichier.pdf",
  "chunk_count": 3,
  "message": "Fichier chiffré avec succès"
}
```

**Exemple avec curl:**
```bash
curl -X POST "http://localhost:8000/encrypt" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/chemin/vers/mon_fichier.pdf"
```

### 2. Déchiffrer un fichier
**GET** `/decrypt/{file_id}?download=true`

Déchiffre un fichier.

**Query Parameters:**
- `download` (bool): Si `true`, télécharge le fichier. Si `false`, retourne le chemin.

**Exemple:**
```bash
# Télécharger le fichier déchiffré
curl -X GET "http://localhost:8000/decrypt/1caeb429419db709?download=true" \
  --output mon_fichier_dechiffre.pdf
```

### 3. Lister tous les fichiers
**GET** `/files`

Retourne la liste de tous les fichiers chiffrés.

**Response:**
```json
[
  {
    "file_id": "1caeb429419db709",
    "original_name": "mon_fichier.pdf",
    "file_size": 1024000,
    "chunk_count": 3,
    "upload_date": "2024-01-15T10:30:00Z"
  }
]
```

### 4. Obtenir les informations d'un fichier
**GET** `/files/{file_id}`

Retourne les détails complets d'un fichier.

**Response:**
```json
{
  "file_id": "1caeb429419db709",
  "name": "mon_fichier.pdf",
  "size": 1024000,
  "encrypted_size": 1024000,
  "algorithm": "AES-256-GCM",
  "chunks": 3,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 5. Supprimer un fichier
**DELETE** `/files/{file_id}?delete_chunks=true`

Supprime un fichier chiffré.

**Query Parameters:**
- `delete_chunks` (bool): Si `true`, supprime aussi les chunks sur le disque.

**Response:**
```json
{
  "message": "Fichier supprimé avec succès",
  "file_id": "1caeb429419db709"
}
```

### 6. Vérification de santé
**GET** `/health`

Vérifie l'état de l'API.

**Response:**
```json
{
  "status": "healthy",
  "service": "MeshDrive Crypto API"
}
```

## Exemple d'utilisation avec Python

```python
import requests

# Chiffrer un fichier
with open('mon_fichier.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/encrypt',
        files={'file': f}
    )
    result = response.json()
    file_id = result['file_id']
    print(f"Fichier chiffré avec l'ID: {file_id}")

# Lister les fichiers
response = requests.get('http://localhost:8000/files')
files = response.json()
print(f"Nombre de fichiers: {len(files)}")

# Déchiffrer un fichier
response = requests.get(
    f'http://localhost:8000/decrypt/{file_id}?download=true'
)
with open('fichier_dechiffre.pdf', 'wb') as f:
    f.write(response.content)
```

## Notes

- Les fichiers chiffrés sont stockés dans le dossier `output/`
- Les métadonnées sont stockées dans le dossier `keys/`
- La bibliothèque `cryptolib` reste utilisable directement sans passer par l'API (compatibilité avec `app.py`)

