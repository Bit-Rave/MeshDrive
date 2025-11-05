# 🔒 Recommandations de Sécurité - MeshDrive Multi-Users

Ce document présente les recommandations de sécurité pour transformer MeshDrive en un système multi-utilisateurs sécurisé.

## 🚨 Problèmes Actuels Identifiés

### 1. **Absence d'Authentification**
- ❌ Aucun système d'identification des utilisateurs
- ❌ Tous les endpoints sont publics
- ❌ N'importe qui peut accéder aux fichiers

### 2. **Absence d'Autorisation**
- ❌ Pas de contrôle d'accès (RBAC/ACL)
- ❌ Tous les utilisateurs voient tous les fichiers
- ❌ Pas de gestion des permissions (lecture/écriture/suppression)

### 3. **Pas d'Isolation des Données**
- ❌ Tous les fichiers dans le même espace (`data/keys/`, `data/chunks/`)
- ❌ Pas de séparation par utilisateur
- ❌ Risque de fuite de données entre utilisateurs

### 4. **CORS Trop Permissif**
- ⚠️ `allow_origins=["*"]` accepte toutes les origines
- ⚠️ Risque de CSRF en production

### 5. **Pas de Validation d'Entrée**
- ⚠️ Pas de protection contre les path traversal (`../`)
- ⚠️ Pas de validation des noms de fichiers
- ⚠️ Risque d'injection de chemins

### 6. **Pas de Rate Limiting**
- ⚠️ Risque de DoS (Denial of Service)
- ⚠️ Pas de limitation de requêtes par utilisateur

### 7. **Pas de Logging d'Audit**
- ⚠️ Pas de traçabilité des actions
- ⚠️ Impossible d'identifier les accès non autorisés

### 8. **Pas de Quotas**
- ⚠️ Pas de limite de stockage par utilisateur
- ⚠️ Risque de saturation du serveur

---

## ✅ Solutions Recommandées

### 1. **Système d'Authentification**

#### Option A : JWT (JSON Web Tokens) - Recommandé
```python
# Dépendances nécessaires
# pip install python-jose[cryptography] passlib[bcrypt] python-multipart

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuration
SECRET_KEY = "your-secret-key-here"  # À générer aléatoirement
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

**Avantages** :
- ✅ Stateless (pas besoin de session serveur)
- ✅ Scalable (fonctionne avec plusieurs serveurs)
- ✅ Standards (RFC 7519)

#### Option B : Sessions avec Redis
- Pour les cas où vous avez besoin de révoquer les tokens rapidement
- Nécessite Redis en infrastructure

**Recommandation** : **JWT** pour commencer, plus simple et adapté à l'architecture actuelle.

---

### 2. **Base de Données Utilisateurs**

```python
# Modèle utilisateur (SQLAlchemy ou similaire)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    quota_bytes = Column(BigInteger, default=1073741824)  # 1 GB par défaut
    used_bytes = Column(BigInteger, default=0)
```

**Options de base de données** :
- **SQLite** : Pour commencer (simple, pas de serveur)
- **PostgreSQL** : Pour la production (plus robuste, meilleures performances)
- **MongoDB** : Alternative NoSQL si vous préférez

**Recommandation** : **SQLite** pour commencer, migration vers **PostgreSQL** en production.

---

### 3. **Isolation des Données par Utilisateur**

#### Structure de stockage proposée :
```
data/
├── users/
│   ├── user_123/
│   │   ├── keys/
│   │   │   └── {file_id}.json
│   │   └── chunks/
│   │       └── {file_id}_chunk_0000.enc
│   ├── user_456/
│   │   └── ...
│   └── ...
```

**Modification de `cryptolib/config.py`** :
```python
def get_user_data_dir(user_id: str) -> Path:
    """Retourne le répertoire de données pour un utilisateur spécifique"""
    return DATA_DIR / "users" / f"user_{user_id}"

def get_user_keys_dir(user_id: str) -> Path:
    """Retourne le répertoire des clés pour un utilisateur spécifique"""
    return get_user_data_dir(user_id) / "keys"

def get_user_chunks_dir(user_id: str) -> Path:
    """Retourne le répertoire des chunks pour un utilisateur spécifique"""
    return get_user_data_dir(user_id) / "chunks"
```

**Avantages** :
- ✅ Isolation complète des données
- ✅ Facilite les backups par utilisateur
- ✅ Facilite la suppression de compte

---

### 4. **Système d'Autorisation (RBAC)**

```python
# Modèle de permissions
class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"

# Vérification des permissions
def check_permission(user: User, file_id: str, permission: Permission) -> bool:
    # Vérifier que le fichier appartient à l'utilisateur
    # ou que l'utilisateur a les permissions de partage
    pass
```

**Niveaux de permissions** :
- **Propriétaire** : Accès complet (lecture/écriture/suppression)
- **Partagé en lecture** : Lecture seule
- **Partagé en écriture** : Lecture + écriture
- **Admin** : Accès à tout (pour la gestion)

---

### 5. **Sécurisation des Endpoints**

#### Middleware d'authentification
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """Vérifie et retourne l'utilisateur actuel"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# Utilisation dans les endpoints
@app.get("/files")
async def list_files(
    current_user: User = Depends(get_current_user),
    folder_path: str = "/"
):
    # Filtrer les fichiers par utilisateur
    user_files = get_files_by_user(current_user.id, folder_path)
    return user_files
```

---

### 6. **Validation des Entrées**

```python
import re
from pathlib import Path

def validate_path(path: str) -> bool:
    """Valide qu'un chemin est sûr (pas de path traversal)"""
    # Normaliser le chemin
    normalized = Path(path).resolve()
    
    # Vérifier qu'il n'y a pas de .. ou de chemins absolus
    if ".." in str(normalized) or str(normalized).startswith("/"):
        return False
    
    # Vérifier les caractères interdits
    if re.search(r'[<>:"|?*\x00-\x1f]', path):
        return False
    
    return True

def validate_filename(filename: str) -> bool:
    """Valide qu'un nom de fichier est sûr"""
    # Longueur maximale
    if len(filename) > 255:
        return False
    
    # Caractères interdits
    forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    if any(char in filename for char in forbidden_chars):
        return False
    
    # Pas de chemins absolus
    if filename.startswith('/') or '\\' in filename:
        return False
    
    return True
```

---

### 7. **Rate Limiting**

```python
# Dépendance : pip install slowapi

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Utilisation
@app.post("/encrypt")
@limiter.limit("10/minute")  # 10 requêtes par minute
async def encrypt_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # ...
```

**Limites recommandées** :
- Upload : 10 fichiers/minute par utilisateur
- Download : 30 requêtes/minute
- API générale : 100 requêtes/minute

---

### 8. **Quotas et Limites**

```python
def check_quota(user: User, file_size: int) -> bool:
    """Vérifie si l'utilisateur a assez d'espace"""
    if user.used_bytes + file_size > user.quota_bytes:
        return False
    return True

# Dans l'endpoint d'upload
@app.post("/encrypt")
async def encrypt_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not check_quota(current_user, file.size):
        raise HTTPException(
            status_code=403,
            detail="Quota de stockage dépassé"
        )
    
    # Upload et mise à jour du quota
    result = encrypt_file(...)
    update_user_quota(current_user.id, file.size)
    return result
```

---

### 9. **Logging d'Audit**

```python
import logging
from datetime import datetime

# Configuration du logging d'audit
audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("logs/audit.log")
audit_logger.addHandler(audit_handler)

def log_action(user_id: int, action: str, resource: str, success: bool):
    """Enregistre une action dans le log d'audit"""
    audit_logger.info(
        f"{datetime.utcnow().isoformat()} | "
        f"User: {user_id} | "
        f"Action: {action} | "
        f"Resource: {resource} | "
        f"Success: {success}"
    )

# Utilisation
@app.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        delete_file_logic(file_id, current_user.id)
        log_action(current_user.id, "DELETE_FILE", file_id, True)
        return {"message": "Fichier supprimé"}
    except Exception as e:
        log_action(current_user.id, "DELETE_FILE", file_id, False)
        raise
```

**Actions à logger** :
- ✅ Connexion/Déconnexion
- ✅ Upload/Download de fichiers
- ✅ Création/Suppression de fichiers/dossiers
- ✅ Partage de fichiers
- ✅ Modifications de permissions
- ✅ Tentatives d'accès non autorisées

---

### 10. **Sécurisation CORS**

```python
# En production
ALLOWED_ORIGINS = [
    "https://meshdrive.example.com",
    "https://www.meshdrive.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Pas de "*" !
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 11. **Chiffrement des Clés Utilisateur**

**Option actuelle** : Les clés sont stockées en clair dans JSON

**Amélioration** : Chiffrer les clés de chiffrement avec une clé maître (dérivée du mot de passe utilisateur)

```python
from cryptography.fernet import Fernet
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Dérive une clé de chiffrement depuis le mot de passe"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_file_key(file_key: str, user_password: str) -> str:
    """Chiffre la clé de fichier avec le mot de passe utilisateur"""
    salt = os.urandom(16)
    key = derive_key_from_password(user_password, salt)
    f = Fernet(key)
    encrypted = f.encrypt(file_key.encode())
    return base64.b64encode(salt + encrypted).decode()
```

**Avantages** :
- ✅ Même avec accès au serveur, impossible de déchiffrer sans mot de passe
- ✅ Chiffrement de bout en bout réel

---

### 12. **HTTPS/TLS**

**En production** :
- ✅ Utiliser HTTPS uniquement
- ✅ Certificats SSL valides (Let's Encrypt gratuit)
- ✅ Redirection HTTP → HTTPS
- ✅ HSTS (HTTP Strict Transport Security)

```python
# Configuration uvicorn avec SSL
uvicorn.run(
    "crypto_api:app",
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

---

### 13. **Protection CSRF**

Avec JWT dans les headers, le risque CSRF est réduit, mais pour plus de sécurité :

```python
# Token CSRF dans les cookies (pour les formulaires)
from fastapi_csrf_protect import CsrfProtect

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings(secret_key=SECRET_KEY)
```

---

### 14. **Validation des Tailles de Fichiers**

```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_TOTAL_FILES = 10000

def validate_file_size(file: UploadFile) -> bool:
    """Valide la taille du fichier"""
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (max: {MAX_FILE_SIZE} bytes)"
        )
    return True
```

---

### 15. **Sanitisation des Noms de Fichiers**

```python
import unicodedata
import re

def sanitize_filename(filename: str) -> str:
    """Nettoie et normalise un nom de fichier"""
    # Normaliser Unicode
    filename = unicodedata.normalize('NFKD', filename)
    
    # Supprimer les caractères non-ASCII problématiques
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remplacer les espaces par des underscores
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    
    # Limiter la longueur
    filename = filename[:255]
    
    return filename.strip('-')
```

---

## 📋 Plan d'Implémentation Recommandé

### Phase 1 : Authentification (Priorité HAUTE)
1. ✅ Ajouter JWT authentication
2. ✅ Créer table utilisateurs (SQLite pour commencer)
3. ✅ Endpoints login/register
4. ✅ Protéger tous les endpoints existants

### Phase 2 : Isolation des Données (Priorité HAUTE)
1. ✅ Modifier `cryptolib` pour isoler par utilisateur
2. ✅ Migrer les données existantes (si nécessaire)
3. ✅ Tester l'isolation complète

### Phase 3 : Autorisation (Priorité MOYENNE)
1. ✅ Système RBAC basique
2. ✅ Permissions par fichier/dossier
3. ✅ Partage de fichiers entre utilisateurs

### Phase 4 : Sécurité Renforcée (Priorité MOYENNE)
1. ✅ Validation des entrées (path traversal, etc.)
2. ✅ Rate limiting
3. ✅ Quotas par utilisateur
4. ✅ Logging d'audit

### Phase 5 : Chiffrement Avancé (Priorité BASSE)
1. ✅ Chiffrement des clés avec mot de passe utilisateur
2. ✅ Clés de chiffrement par utilisateur

---

## 🛠️ Dépendances Nécessaires

```bash
# Authentification
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install python-multipart

# Base de données
pip install sqlalchemy
pip install alembic  # Pour les migrations

# Rate limiting
pip install slowapi

# Validation
pip install pydantic[email]  # Validation d'email

# HTTPS (production)
pip install uvicorn[standard]
```

---

## 📚 Ressources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [Python Security](https://python.readthedocs.io/en/latest/library/security.html)

---

## ⚠️ Notes Importantes

1. **Ne jamais stocker les mots de passe en clair** : Toujours utiliser bcrypt/argon2
2. **Rotate les secrets régulièrement** : Changer SECRET_KEY périodiquement
3. **Backup régulier** : Sauvegarder `data/` et la base de données
4. **Monitoring** : Surveiller les logs d'audit pour détecter les anomalies
5. **Tests de sécurité** : Effectuer des audits de sécurité réguliers

---

**Dernière mise à jour** : 2024

