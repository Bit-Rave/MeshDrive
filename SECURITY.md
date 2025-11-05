# 🔒 Recommandations de Sécurité - MeshDrive Multi-Users

Ce document présente les recommandations de sécurité pour transformer MeshDrive en un système multi-utilisateurs sécurisé.

## 🚨 Problèmes Actuels Identifiés

### 1. **Absence d'Authentification** ✅ **RÉSOLU**
- ✅ Système d'identification JWT implémenté
- ✅ Tous les endpoints sont protégés
- ✅ Authentification requise pour accéder aux fichiers

### 2. **Absence d'Autorisation** ⚠️ **PARTIELLEMENT RÉSOLU**
- ✅ Contrôle d'accès basique (isolation par utilisateur)
- ✅ Chaque utilisateur voit uniquement ses fichiers
- ⚠️ Pas de gestion des permissions (lecture/écriture/suppression) - RBAC complet à venir
- ⚠️ Pas de partage de fichiers entre utilisateurs - à implémenter

### 3. **Pas d'Isolation des Données** ✅ **RÉSOLU**
- ✅ Fichiers isolés par utilisateur (`data/users/user_{id}/keys/`, `data/users/user_{id}/chunks/`)
- ✅ Séparation complète par utilisateur
- ✅ Pas de fuite de données entre utilisateurs

### 4. **CORS Trop Permissif** ⚠️ **PARTIELLEMENT RÉSOLU**
- ✅ `allow_origins` configuré avec des origines spécifiques (localhost/dev)
- ⚠️ À configurer avec les origines de production en production

### 5. **Pas de Validation d'Entrée** ✅ **RÉSOLU**
- ✅ Protection contre les path traversal (`../`)
- ✅ Validation des noms de fichiers
- ✅ Sanitisation des chemins et noms de fichiers
- ✅ Protection contre l'injection de chemins

### 6. **Pas de Rate Limiting** ❌ **NON RÉSOLU**
- ⚠️ Risque de DoS (Denial of Service)
- ⚠️ Pas de limitation de requêtes par utilisateur
- 📝 **TODO** : Implémenter rate limiting avec `slowapi`

### 7. **Pas de Logging d'Audit** ✅ **RÉSOLU**
- ✅ Traçabilité complète des actions utilisateur
- ✅ Logging structuré avec IP, utilisateur, succès/échec
- ✅ Détection des tentatives d'accès non autorisées
- ✅ Fichier de log : `data/logs/audit.log`

### 8. **Pas de Quotas** ✅ **RÉSOLU**
- ✅ Limite de stockage par utilisateur (1 GB par défaut)
- ✅ Vérification du quota avant chaque upload
- ✅ Mise à jour automatique du quota utilisé

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

### 6. **Validation des Entrées** ✅ **IMPLÉMENTÉ**

**Module** : `core/security/validation.py`

**Fonctionnalités implémentées** :
- ✅ `validate_path()` : Protection contre path traversal
- ✅ `validate_folder_path()` : Validation des chemins de dossiers
- ✅ `validate_filename()` : Validation des noms de fichiers
- ✅ `sanitize_filename()` : Sanitisation et normalisation Unicode
- ✅ `validate_file_size()` : Validation des tailles de fichiers (100 MB max)
- ✅ `validate_and_sanitize_filename()` : Validation + sanitisation en une opération
- ✅ `validate_and_sanitize_folder_path()` : Validation + normalisation des chemins

**Intégration** : Toutes les routes API valident automatiquement les entrées utilisateur.

```python
# Exemple d'utilisation dans les routes
from core.security import validate_and_sanitize_folder_path, validate_and_sanitize_filename

folder_path = validate_and_sanitize_folder_path(folder_path)
file.filename = validate_and_sanitize_filename(file.filename)
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

### 9. **Logging d'Audit** ✅ **IMPLÉMENTÉ**

**Module** : `core/security/audit.py`

**Fonctionnalités implémentées** :
- ✅ Logger d'audit structuré avec format standardisé
- ✅ Fichier de log : `data/logs/audit.log`
- ✅ Enregistrement de l'IP client, utilisateur, action, ressource, succès/échec
- ✅ Types d'actions auditables : `AuditAction` enum (LOGIN, LOGOUT, REGISTER, FILE_UPLOAD, FILE_DOWNLOAD, etc.)

**Actions loggées** :
- ✅ Connexion/Déconnexion (LOGIN, LOGOUT)
- ✅ Inscription (REGISTER)
- ✅ Upload/Download de fichiers (FILE_UPLOAD, FILE_DOWNLOAD)
- ✅ Création/Suppression de fichiers/dossiers (FILE_DELETE, FILE_MOVE, FOLDER_CREATE, FOLDER_DELETE)
- ✅ Téléchargement de dossiers (FOLDER_DOWNLOAD)
- ✅ Tentatives d'accès non autorisées (ACCESS_DENIED, INVALID_TOKEN)
- ✅ Tentatives de path traversal (PATH_TRAVERSAL_ATTEMPT)
- ✅ Quota dépassé (QUOTA_EXCEEDED)
- ✅ Fichiers trop volumineux (FILE_TOO_LARGE)
- ✅ Noms de fichiers invalides (INVALID_FILENAME)

**Intégration** : Toutes les routes API loggent automatiquement les actions utilisateur.

```python
# Exemple d'utilisation
from core.security import log_user_action, AuditAction, get_client_ip

log_user_action(
    current_user,
    AuditAction.FILE_UPLOAD,
    resource=file_id,
    success=True,
    details="Filename: example.txt",
    ip_address=get_client_ip(request)
)
```

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
    "api.app:app",
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

### 14. **Validation des Tailles de Fichiers** ✅ **IMPLÉMENTÉ**

**Module** : `core/security/validation.py`

**Fonctionnalités implémentées** :
- ✅ `MAX_FILE_SIZE = 100 * 1024 * 1024` (100 MB par défaut)
- ✅ `validate_file_size()` : Validation de la taille des fichiers uploadés
- ✅ Intégration automatique dans les routes d'upload
- ✅ Logging d'audit pour les fichiers trop volumineux

**Intégration** : Toutes les routes d'upload valident automatiquement la taille des fichiers.

```python
# Exemple d'utilisation
from core.security import validate_file_size

validate_file_size(file)  # Lève HTTPException 413 si trop volumineux
```

---

### 15. **Sanitisation des Noms de Fichiers** ✅ **IMPLÉMENTÉ**

**Module** : `core/security/validation.py`

**Fonctionnalités implémentées** :
- ✅ `sanitize_filename()` : Normalisation Unicode (NFKD), nettoyage des caractères, limitation de longueur
- ✅ `validate_and_sanitize_filename()` : Validation + sanitisation en une opération
- ✅ Protection contre les noms réservés Windows (CON, PRN, AUX, etc.)
- ✅ Suppression des caractères de contrôle et caractères interdits
- ✅ Limitation à 255 caractères (avec préservation de l'extension si possible)

**Intégration** : Tous les noms de fichiers sont automatiquement sanitized avant traitement.

```python
# Exemple d'utilisation
from core.security import validate_and_sanitize_filename

file.filename = validate_and_sanitize_filename(file.filename)
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
1. ✅ Système RBAC basique - **IMPLÉMENTÉ** (isolation par utilisateur)
2. ⚠️ Permissions par fichier/dossier - **PARTIELLEMENT** (propriétaire uniquement)
3. ❌ Partage de fichiers entre utilisateurs - **À IMPLÉMENTER**

### Phase 4 : Sécurité Renforcée (Priorité MOYENNE)
1. ✅ Validation des entrées (path traversal, etc.) - **IMPLÉMENTÉ**
2. ❌ Rate limiting - **À IMPLÉMENTER**
3. ✅ Quotas par utilisateur - **IMPLÉMENTÉ**
4. ✅ Logging d'audit - **IMPLÉMENTÉ**

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

**Dernière mise à jour** : 2025-01-11

---

## 🌐 Datacenter Décentralisé - Architecture Zero-Knowledge

MeshDrive est conçu comme un **datacenter décentralisé** où n'importe qui peut héberger un serveur. Pour garantir que les données utilisateur ne fuient jamais, même si l'hébergeur est malveillant, le système doit respecter une architecture **zero-knowledge**.

### ⚠️ Problèmes Critiques pour un Datacenter Décentralisé

#### 1. **Clés de Chiffrement Stockées en Clair** ❌ **CRITIQUE**
- ❌ Les clés de chiffrement sont stockées en clair dans `data/users/user_{id}/keys/{file_id}.json`
- ❌ Un hébergeur malveillant peut accéder à toutes les clés et déchiffrer tous les fichiers
- ❌ **RISQUE** : Fuite complète des données utilisateur

#### 2. **Serveur Peut Déchiffrer les Données** ❌ **CRITIQUE**
- ❌ Le serveur peut déchiffrer les fichiers car il a accès aux clés
- ❌ Aucune protection contre un hébergeur malveillant
- ❌ **RISQUE** : Pas de confidentialité réelle

#### 3. **Pas de Vérification d'Intégrité** ⚠️ **MOYEN**
- ⚠️ Pas de vérification que le serveur n'a pas modifié les données
- ⚠️ Risque de corruption ou manipulation malveillante
- ⚠️ **RISQUE** : Données corrompues ou manipulées

#### 4. **Métadonnées Non Chiffrées** ⚠️ **MOYEN**
- ⚠️ Les noms de fichiers sont stockés en clair dans les métadonnées
- ⚠️ Un hébergeur peut voir les noms de fichiers même sans accès au contenu
- ⚠️ **RISQUE** : Fuite d'informations sur les fichiers

---

## ✅ Solutions pour Datacenter Décentralisé

### 1. **Chiffrement des Clés avec Mot de Passe Utilisateur** ✅ **À IMPLÉMENTER**

**Principe** : Les clés de chiffrement des fichiers sont elles-mêmes chiffrées avec une clé maître dérivée du mot de passe utilisateur.

```python
# Côté client (avant envoi au serveur)
def encrypt_file_key(file_key: bytes, user_password: str) -> str:
    """
    Chiffre la clé de fichier avec le mot de passe utilisateur
    Le serveur ne peut jamais déchiffrer cette clé sans le mot de passe
    """
    # Dériver une clé depuis le mot de passe
    salt = os.urandom(16)
    master_key = derive_key_from_password(user_password, salt)
    
    # Chiffrer la clé de fichier avec la clé maître
    f = Fernet(master_key)
    encrypted_key = f.encrypt(file_key)
    
    # Retourner salt + clé chiffrée (base64)
    return base64.b64encode(salt + encrypted_key).decode()
```

**Avantages** :
- ✅ Le serveur ne peut jamais déchiffrer les clés sans le mot de passe
- ✅ Même avec accès au serveur, impossible de déchiffrer les fichiers
- ✅ Architecture zero-knowledge : le serveur ne sait rien du contenu

**Architecture** :
```
Client:
  1. Génère clé de fichier (AES-256)
  2. Chiffre le fichier avec cette clé
  3. Chiffre la clé avec le mot de passe utilisateur
  4. Envoie fichier chiffré + clé chiffrée au serveur

Serveur:
  - Stocke uniquement des données chiffrées
  - Ne peut jamais déchiffrer les clés
  - Ne peut jamais déchiffrer les fichiers

Client (déconnexion):
  1. Demande fichier chiffré + clé chiffrée au serveur
  2. Déchiffre la clé avec son mot de passe
  3. Déchiffre le fichier avec la clé
```

### 2. **Chiffrement des Métadonnées** ✅ **À IMPLÉMENTER**

**Principe** : Chiffrer aussi les noms de fichiers et métadonnées sensibles.

```python
def encrypt_metadata(metadata: dict, user_password: str) -> str:
    """
    Chiffre les métadonnées (nom de fichier, etc.) avec le mot de passe
    """
    master_key = derive_key_from_password(user_password, salt)
    f = Fernet(master_key)
    
    # Chiffrer les métadonnées sensibles
    sensitive_data = {
        'original_name': metadata['original_name'],
        'folder_path': metadata['folder_path']
    }
    
    encrypted_metadata = f.encrypt(json.dumps(sensitive_data).encode())
    return base64.b64encode(encrypted_metadata).decode()
```

**Métadonnées à chiffrer** :
- ✅ Nom de fichier (`original_name`)
- ✅ Chemin du dossier (`folder_path`)
- ✅ Taille originale (optionnel, peut révéler des infos)

**Métadonnées non chiffrées** (nécessaires pour le serveur) :
- File ID (hash du fichier chiffré)
- Taille chiffrée
- Hash des chunks
- Date de création

### 3. **Vérification d'Intégrité des Données** ✅ **À IMPLÉMENTER**

**Principe** : Vérifier que le serveur n'a pas modifié les données.

```python
def verify_file_integrity(file_id: str, decrypted_data: bytes, metadata: dict) -> bool:
    """
    Vérifie l'intégrité du fichier déchiffré
    """
    # Recalculer le hash
    calculated_hash = hashlib.sha256(decrypted_data).hexdigest()
    
    # Comparer avec le hash stocké dans les métadonnées
    stored_hash = metadata.get('integrity_hash')
    
    if stored_hash and calculated_hash != stored_hash:
        raise ValueError("Fichier corrompu ou modifié")
    
    return True
```

**Implantation** :
- ✅ Stocker un hash d'intégrité (SHA-256) du fichier déchiffré dans les métadonnées
- ✅ Vérifier ce hash après déchiffrement
- ✅ Détecter toute modification ou corruption

### 4. **Protection contre les Serveurs Malveillants** ✅ **À IMPLÉMENTER**

**Mesures à implémenter** :

1. **Chiffrement côté client** :
   - ✅ Tous les fichiers sont chiffrés AVANT d'être envoyés au serveur
   - ✅ Les clés sont chiffrées AVANT d'être envoyées au serveur
   - ✅ Le serveur ne voit jamais de données en clair

2. **Vérification des données reçues** :
   - ✅ Vérifier l'intégrité des chunks téléchargés
   - ✅ Vérifier que les métadonnées n'ont pas été modifiées
   - ✅ Détecter toute tentative de manipulation

3. **Pas de clés en clair sur le serveur** :
   - ✅ Toutes les clés sont chiffrées avec le mot de passe utilisateur
   - ✅ Le serveur ne peut jamais déchiffrer les clés
   - ✅ Architecture zero-knowledge garantie

4. **Isolation par utilisateur** :
   - ✅ Chaque utilisateur a ses propres clés chiffrées
   - ✅ Même si un utilisateur est compromis, les autres sont protégés
   - ✅ Pas de fuite de données entre utilisateurs

---

## 📋 Plan d'Implémentation Zero-Knowledge

### Phase 1 : Chiffrement des Clés (Priorité CRITIQUE)
1. ✅ Dériver une clé maître depuis le mot de passe utilisateur
2. ✅ Chiffrer toutes les clés de fichiers avec la clé maître
3. ✅ Modifier le système pour stocker uniquement des clés chiffrées
4. ✅ Modifier le déchiffrement pour déchiffrer d'abord la clé

### Phase 2 : Chiffrement des Métadonnées (Priorité HAUTE)
1. ✅ Chiffrer les noms de fichiers
2. ✅ Chiffrer les chemins de dossiers
3. ✅ Garder uniquement les métadonnées nécessaires au serveur en clair

### Phase 3 : Vérification d'Intégrité (Priorité HAUTE)
1. ✅ Calculer et stocker un hash d'intégrité
2. ✅ Vérifier l'intégrité lors du déchiffrement
3. ✅ Détecter toute modification ou corruption

### Phase 4 : Protection Avancée (Priorité MOYENNE)
1. ✅ Chiffrement des noms de dossiers
2. ✅ Vérification de l'intégrité des chunks individuels
3. ✅ Signature cryptographique des métadonnées

---

## 🔒 Garanties de Sécurité pour Datacenter Décentralisé

### ✅ Garanties Actuelles
- ✅ Isolation des données par utilisateur
- ✅ Chiffrement AES-256-GCM des fichiers
- ✅ Authentification JWT requise

### ❌ Garanties Manquantes (CRITIQUE)
- ❌ **ZERO-KNOWLEDGE** : Le serveur peut actuellement déchiffrer les fichiers
- ❌ **Clés chiffrées** : Les clés sont stockées en clair
- ❌ **Métadonnées chiffrées** : Les noms de fichiers sont en clair
- ❌ **Vérification d'intégrité** : Pas de vérification que le serveur n'a pas modifié les données

### 🎯 Objectif Final
**Architecture Zero-Knowledge** : Le serveur ne peut jamais accéder au contenu des fichiers, même s'il est malveillant.

---

### ⚠️ **IMPORTANT : Architecture Actuelle vs Architecture Zero-Knowledge**

**Architecture Actuelle** (⚠️ NON SÉCURISÉE pour datacenter décentralisé) :
- ❌ Chiffrement effectué côté **serveur**
- ❌ Clés de chiffrement stockées **en clair** sur le serveur
- ❌ Le serveur peut déchiffrer tous les fichiers
- ❌ **RISQUE** : Un hébergeur malveillant peut accéder à toutes les données

**Architecture Zero-Knowledge Requise** (✅ SÉCURISÉE pour datacenter décentralisé) :
- ✅ Chiffrement effectué côté **client** (JavaScript)
- ✅ Clés de chiffrement chiffrées avec le **mot de passe utilisateur**
- ✅ Le serveur ne stocke que des données **déjà chiffrées**
- ✅ Le serveur ne peut jamais déchiffrer les fichiers
- ✅ **SÉCURITÉ** : Même un hébergeur malveillant ne peut pas accéder aux données

**Module Implémenté** : `cryptolib/key_encryption.py`
- ✅ Fonctions pour chiffrer/déchiffrer les clés avec mot de passe
- ✅ Fonctions pour chiffrer/déchiffrer les métadonnées
- ✅ Fonctions de vérification d'intégrité
- ⚠️ **À INTÉGRER** : Ces fonctions doivent être utilisées côté client avant l'envoi au serveur

**Prochaines Étapes** :
1. ✅ Implémenter le chiffrement côté client (JavaScript) - **IMPLÉMENTÉ**
2. ✅ Modifier le frontend pour chiffrer les fichiers avant l'envoi - **IMPLÉMENTÉ**
3. ✅ Modifier le backend pour stocker uniquement des clés chiffrées - **IMPLÉMENTÉ**
4. ✅ Modifier le déchiffrement pour déchiffrer les clés côté client - **IMPLÉMENTÉ**
5. ✅ Optimiser la détection du type de chiffrement - **IMPLÉMENTÉ**
   - Vérification des métadonnées avant d'appeler `/api/client-decrypt/`
   - Évite les requêtes inutiles pour les fichiers chiffrés serveur
6. ✅ Correction des problèmes de boucle infinie lors du téléchargement - **IMPLÉMENTÉ**
   - Gestion correcte des erreurs 404/400
   - Détection automatique du type de fichier (chiffré côté client vs serveur)

**Fichiers Créés** :
- ✅ `web/js/crypto.js` : Module JavaScript de chiffrement côté client
- ✅ `cryptolib/key_encryption.py` : Module Python pour chiffrement des clés avec mot de passe
- ✅ `api/services/client_encrypted_service.py` : Service pour gérer les fichiers chiffrés côté client

**Fichiers Modifiés** :
- ✅ `web/js/dragdrop.js` : Chiffrement des fichiers avant l'envoi
- ✅ `web/js/auth.js` : Gestion du mot de passe en sessionStorage
- ✅ `web/js/config.js` : Ajout de STORAGE_KEYS.password
- ✅ `api/routes/multipart_files.py` : Support des fichiers chiffrés côté client
- ✅ `cryptolib/metadata_manager.py` : Méthode pour sauvegarder les métadonnées avec clés chiffrées
- ✅ `web/js/api.js` : Optimisation de `decryptFileAPI()` pour éviter les requêtes inutiles
  - Utilisation des métadonnées du fichier pour détecter le type de chiffrement
  - Gestion améliorée des erreurs 404/400
  - Correction des boucles infinies lors du téléchargement
- ✅ `web/js/files.js` : Passage des métadonnées du fichier à `decryptFileAPI()`
  - Suppression des appels `showLoading()`/`hideLoading()` inutiles
- ✅ `web/js/ui.js` : Amélioration de `hideLoading()` pour éviter les messages "Chargement..." en boucle

---

## 📊 État d'Implémentation

### ✅ Implémenté
- ✅ Authentification JWT
- ✅ Base de données utilisateurs (SQLite)
- ✅ Isolation des données par utilisateur
- ✅ Sécurisation des endpoints (authentification requise)
- ✅ Validation des entrées (path traversal, noms de fichiers)
- ✅ Sanitisation des noms de fichiers
- ✅ Validation des tailles de fichiers (100 MB max)
- ✅ Quotas par utilisateur (1 GB par défaut)
- ✅ Logging d'audit complet
- ✅ CORS configuré (localhost/dev)

### ⚠️ Partiellement Implémenté
- ⚠️ Autorisation : Isolation basique (propriétaire uniquement), pas de RBAC complet
- ⚠️ CORS : Configuré pour dev, à ajuster pour production

### ❌ À Implémenter
- ✅ **CRITIQUE** : Architecture Zero-Knowledge (chiffrement côté client) - **IMPLÉMENTÉ**
- ✅ **CRITIQUE** : Chiffrement des clés avec mot de passe utilisateur - **IMPLÉMENTÉ**
- ✅ **CRITIQUE** : Chiffrement des métadonnées (noms de fichiers) - **IMPLÉMENTÉ**
- ✅ **CRITIQUE** : Vérification d'intégrité des données - **IMPLÉMENTÉ**
- ✅ **CRITIQUE** : Déchiffrement côté client pour les fichiers chiffrés côté client - **IMPLÉMENTÉ**
- ✅ **Optimisation** : Détection intelligente du type de chiffrement (côté client vs serveur) - **IMPLÉMENTÉ**
  - Évite les requêtes API inutiles en vérifiant les métadonnées avant d'appeler `/api/client-decrypt/`
  - Réduit l'exposition des endpoints et améliore les performances
- ✅ **Optimisation** : Gestion améliorée des erreurs lors du téléchargement - **IMPLÉMENTÉ**
  - Correction des boucles infinies lors du téléchargement
  - Gestion correcte des états de chargement
- ❌ Rate limiting (DoS protection)
- ❌ Partage de fichiers entre utilisateurs
- ❌ Système RBAC complet avec permissions granulaire
- ❌ HTTPS/TLS (production)
- ❌ Protection CSRF (token CSRF)
- ❌ HSTS (HTTP Strict Transport Security)

