# 🔐 Cryptolib - Bibliothèque de chiffrement MeshDrive

Bibliothèque Python pour le chiffrement, le déchiffrement et la gestion de fichiers sécurisés avec AES-256-GCM.

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Exemples](#exemples)

## 🎯 Vue d'ensemble

`cryptolib` est une bibliothèque complète pour la gestion sécurisée de fichiers chiffrés. Elle fournit :

- ✅ **Chiffrement AES-256-GCM** : Chiffrement de bout en bout avec AES-256-GCM
- ✅ **Découpage en chunks** : Fichiers divisés en chunks de 1 Mo pour une gestion optimale
- ✅ **Gestion des métadonnées** : Stockage sécurisé des clés et métadonnées
- ✅ **Gestion des dossiers** : Organisation hiérarchique des fichiers
- ✅ **Intégrité vérifiée** : Vérification de l'intégrité des données avec SHA-256

## 📦 Installation

Aucune installation spécifique requise. La bibliothèque fait partie du projet MeshDrive.

### Dépendances

```bash
pip install cryptography pydantic
```

## 🚀 Utilisation rapide

### Exemple basique

```python
from cryptolib import CryptoSystem

# Initialisation
crypto = CryptoSystem()

# Chiffrer un fichier
result = crypto.encrypt_file("mon_fichier.pdf", folder_path="/")

# Déchiffrer un fichier
output_path = crypto.decrypt_file(result['file_id'], "fichier_dechiffre.pdf")

# Lister les fichiers
files = crypto.list_files("/")

# Créer un dossier
folder = crypto.create_folder("Documents", "/")

# Obtenir le contenu d'un dossier
contents = crypto.get_folder_contents("/Documents")
```

## 🏗️ Architecture

### Structure des composants

```
CryptoSystem (Point d'entrée principal)
├── Encryptor          → Chiffrement des fichiers
├── Decryptor          → Déchiffrement des fichiers
├── ChunkManager       → Découpage et réassemblage
├── MetadataManager    → Gestion des métadonnées
└── FolderManager      → Gestion des dossiers
```

### Flux de chiffrement

1. **Lecture du fichier** → Données brutes
2. **Génération clé + nonce** → Clé AES-256 et nonce
3. **Chiffrement** → Données chiffrées avec AES-256-GCM
4. **Génération file_id** → Hash SHA-256 des données chiffrées
5. **Découpage en chunks** → Chunks de 1 Mo
6. **Sauvegarde** → Chunks sur disque + métadonnées JSON

### Flux de déchiffrement

1. **Chargement métadonnées** → Récupération de la clé et du nonce
2. **Chargement des chunks** → Lecture des chunks depuis le disque
3. **Réassemblage** → Reconstruction des données chiffrées
4. **Vérification intégrité** → Hash SHA-256
5. **Déchiffrement** → Données en clair
6. **Sauvegarde** → Fichier déchiffré

## 📚 API Reference

### Classe principale : `CryptoSystem`

Point d'entrée principal pour toutes les opérations.

#### Méthodes de chiffrement/déchiffrement

##### `encrypt_file(file_path, folder_path="/", original_name=None)`

Chiffre un fichier et le stocke dans le système.

**Paramètres :**
- `file_path` (str) : Chemin vers le fichier à chiffrer
- `folder_path` (str) : Chemin du dossier de destination (par défaut "/")
- `original_name` (str, optionnel) : Nom original du fichier

**Retourne :**
```python
{
    'file_id': str,           # ID unique du fichier
    'original_name': str,     # Nom original
    'chunks': List[Dict],     # Liste des chunks créés
    'metadata': FileMetadata, # Métadonnées
    'folder_path': str        # Chemin du dossier
}
```

**Exemple :**
```python
result = crypto.encrypt_file("document.pdf", folder_path="/Documents")
print(f"Fichier chiffré avec ID: {result['file_id']}")
```

##### `decrypt_file(file_id, output_path=None)`

Déchiffre un fichier et le sauvegarde.

**Paramètres :**
- `file_id` (str) : ID du fichier à déchiffrer
- `output_path` (str, optionnel) : Chemin de sauvegarde

**Retourne :**
- `str` : Chemin du fichier déchiffré

**Exemple :**
```python
output = crypto.decrypt_file("b8986cbc629a0cc6", "document_dechiffre.pdf")
print(f"Fichier déchiffré: {output}")
```

#### Méthodes de gestion des fichiers

##### `list_files(folder_path="/")`

Liste tous les fichiers dans un dossier.

**Paramètres :**
- `folder_path` (str) : Chemin du dossier (par défaut "/")

**Retourne :**
```python
[
    {
        'file_id': str,
        'original_name': str,
        'file_size': int,
        'chunk_count': int,
        'upload_date': str,
        'folder_path': str
    },
    ...
]
```

##### `get_file_info(file_id)`

Récupère les informations détaillées d'un fichier.

**Paramètres :**
- `file_id` (str) : ID du fichier

**Retourne :**
```python
{
    'file_id': str,
    'name': str,
    'size': int,
    'encrypted_size': int,
    'algorithm': str,
    'chunks': int,
    'created_at': str
}
```

##### `move_file(file_id, new_folder_path)`

Déplace un fichier vers un nouveau dossier.

**Paramètres :**
- `file_id` (str) : ID du fichier
- `new_folder_path` (str) : Nouveau chemin du dossier

**Retourne :**
- `bool` : True si le déplacement a réussi

##### `delete_file(file_id, delete_chunks=True)`

Supprime un fichier et ses chunks.

**Paramètres :**
- `file_id` (str) : ID du fichier
- `delete_chunks` (bool) : Si True, supprime aussi les chunks sur le disque

#### Méthodes de gestion des dossiers

##### `create_folder(folder_name, parent_path="/")`

Crée un nouveau dossier.

**Paramètres :**
- `folder_name` (str) : Nom du dossier
- `parent_path` (str) : Chemin du dossier parent (par défaut "/")

**Retourne :**
- `FolderMetadata` : Métadonnées du dossier créé

**Exemple :**
```python
folder = crypto.create_folder("Documents", "/")
print(f"Dossier créé: {folder.folder_path}")
```

##### `list_folders(parent_path="/")`

Liste tous les dossiers dans un dossier parent.

**Paramètres :**
- `parent_path` (str) : Chemin du dossier parent

**Retourne :**
```python
[
    {
        'folder_id': str,
        'folder_name': str,
        'folder_path': str,
        'parent_path': str,
        'created_at': str
    },
    ...
]
```

##### `get_folder(folder_path)`

Récupère les métadonnées d'un dossier.

**Paramètres :**
- `folder_path` (str) : Chemin du dossier

**Retourne :**
- `Dict` ou `None` : Métadonnées du dossier ou None si introuvable

##### `delete_folder(folder_path, recursive=False)`

Supprime un dossier.

**Paramètres :**
- `folder_path` (str) : Chemin du dossier
- `recursive` (bool) : Si True, supprime aussi les sous-dossiers et fichiers

**Retourne :**
- `bool` : True si le dossier a été supprimé

##### `get_folder_contents(folder_path="/")`

Récupère le contenu d'un dossier (fichiers et sous-dossiers).

**Paramètres :**
- `folder_path` (str) : Chemin du dossier

**Retourne :**
```python
{
    'files': List[Dict],    # Liste des fichiers
    'folders': List[Dict]   # Liste des dossiers
}
```

## ⚙️ Configuration

### Fichier `config.py`

La configuration se trouve dans `cryptolib/config.py` :

```python
# Répertoires de stockage
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = DATA_DIR / "keys"      # Métadonnées JSON
CHUNKS_DIR = DATA_DIR / "chunks"  # Fichiers chiffrés

# Taille des chunks (1 MB par défaut)
CHUNK_SIZE = 1024 * 1024

# Algorithme de chiffrement
ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_SIZE_BITS = 256
NONCE_SIZE_BITS = 96
```

### Emplacement des fichiers

- **Métadonnées** : `data/keys/{file_id}.json`
- **Chunks chiffrés** : `data/chunks/{file_id}_chunk_{index:04d}.enc`
- **Métadonnées dossiers** : `data/keys/_folders/{folder_id}.json`

## 💡 Exemples

### Exemple 1 : Chiffrer et déchiffrer un fichier

```python
from cryptolib import CryptoSystem

crypto = CryptoSystem()

# Chiffrer
result = crypto.encrypt_file("important.pdf", folder_path="/Documents")
print(f"Fichier chiffré: {result['file_id']}")

# Déchiffrer
output = crypto.decrypt_file(result['file_id'], "important_dechiffre.pdf")
print(f"Fichier déchiffré: {output}")
```

### Exemple 2 : Organiser des fichiers dans des dossiers

```python
from cryptolib import CryptoSystem

crypto = CryptoSystem()

# Créer une structure de dossiers
crypto.create_folder("Documents", "/")
crypto.create_folder("Photos", "/")
crypto.create_folder("2024", "/Photos")

# Chiffrer des fichiers dans différents dossiers
crypto.encrypt_file("rapport.pdf", folder_path="/Documents")
crypto.encrypt_file("vacances.jpg", folder_path="/Photos/2024")

# Lister le contenu
contents = crypto.get_folder_contents("/")
print(f"Fichiers: {len(contents['files'])}")
print(f"Dossiers: {len(contents['folders'])}")
```

### Exemple 3 : Déplacer et supprimer des fichiers

```python
from cryptolib import CryptoSystem

crypto = CryptoSystem()

# Chiffrer un fichier
result = crypto.encrypt_file("temp.txt", folder_path="/")

# Déplacer vers un dossier
crypto.move_file(result['file_id'], "/Documents")

# Supprimer le fichier
crypto.delete_file(result['file_id'], delete_chunks=True)
```

### Exemple 4 : Lister tous les fichiers

```python
from cryptolib import CryptoSystem

crypto = CryptoSystem()

# Lister les fichiers dans un dossier
files = crypto.list_files("/Documents")
for file in files:
    print(f"{file['original_name']} ({file['file_size']} bytes)")

# Lister tous les fichiers (tous dossiers)
all_files = crypto.list_all_files()
print(f"Total: {len(all_files)} fichiers")
```

## 🔒 Sécurité

### Chiffrement

- **Algorithme** : AES-256-GCM (Galois/Counter Mode)
- **Taille de clé** : 256 bits
- **Nonce** : 96 bits (généré aléatoirement)
- **Authentification** : Intégrée dans GCM

### Intégrité

- **Vérification hash** : SHA-256 pour chaque chunk
- **File ID** : Basé sur le hash SHA-256 des données chiffrées
- **Vérification lors du déchiffrement** : Hash recalculé et comparé

### Stockage

- **Clés** : Stockées dans `data/keys/` (JSON chiffré)
- **Chunks** : Stockés dans `data/chunks/` (fichiers .enc)
- **Métadonnées** : Incluent toutes les informations nécessaires au déchiffrement

## 📁 Structure des fichiers

### Métadonnées JSON (`data/keys/{file_id}.json`)

```json
{
  "file_id": "b8986cbc629a0cc6",
  "original_name": "document.pdf",
  "original_size": 1024000,
  "encrypted_size": 1024064,
  "encryption": {
    "algorithm": "AES-256-GCM",
    "key": "hex_encoded_key",
    "nonce": "hex_encoded_nonce",
    "key_size_bits": 256,
    "nonce_size_bits": 96
  },
  "chunks": [
    {
      "chunk_id": "abc123",
      "hash": "sha256_hash",
      "size": 1048576,
      "index": 0,
      "file_path": "data/chunks/b8986cbc629a0cc6_chunk_0000.enc"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "folder_path": "/Documents"
}
```

## 🛠️ Composants internes

### `Encryptor`

Gère le chiffrement des fichiers avec AES-256-GCM.

**Méthodes principales :**
- `encrypt_file()` : Chiffre un fichier complet

### `Decryptor`

Gère le déchiffrement des fichiers.

**Méthodes principales :**
- `decrypt_file()` : Déchiffre un fichier

### `ChunkManager`

Gère le découpage et le réassemblage des fichiers en chunks.

**Méthodes principales :**
- `split_into_chunks()` : Découpe les données en chunks
- `load_chunks_from_disk()` : Charge les chunks depuis le disque
- `reassemble_chunks()` : Réassemble les chunks
- `delete_chunks()` : Supprime les chunks

### `MetadataManager`

Gère la sauvegarde et le chargement des métadonnées.

**Méthodes principales :**
- `save_metadata()` : Sauvegarde les métadonnées
- `load_metadata()` : Charge les métadonnées
- `list_files()` : Liste les fichiers
- `get_file_info()` : Récupère les infos d'un fichier
- `update_file_folder_path()` : Met à jour le dossier d'un fichier

### `FolderManager`

Gère la création et la gestion des dossiers.

**Méthodes principales :**
- `create_folder()` : Crée un dossier
- `get_folder()` : Récupère un dossier
- `list_folders()` : Liste les dossiers
- `delete_folder()` : Supprime un dossier

## 📝 Modèles de données

### Modèles dataclass (internes)

- `EncryptedChunk` : Représente un chunk chiffré
- `FileMetadata` : Métadonnées d'un fichier chiffré
- `FolderMetadata` : Métadonnées d'un dossier

### Modèles Pydantic (API)

- `FileInfo` : Informations sur un fichier
- `FileDetails` : Détails complets d'un fichier
- `EncryptResponse` : Réponse après chiffrement
- `FolderInfo` : Informations sur un dossier
- `CreateFolderRequest` : Requête de création de dossier
- `MoveFileRequest` : Requête de déplacement
- `DecryptResponse` : Réponse après déchiffrement

## 🚨 Gestion des erreurs

### Exceptions courantes

```python
# Fichier introuvable
FileNotFoundError: "❌ Fichier introuvable: {file_path}"

# Métadonnées introuvables
FileNotFoundError: "❌ Métadonnées introuvables pour {file_id}"

# Corruption détectée
ValueError: "❌ CORRUPTION DÉTECTÉE!"

# Dossier introuvable
ValueError: "❌ Dossier de destination introuvable: {folder_path}"

# Déchiffrement échoué
ValueError: "❌ Déchiffrement échoué!"
```

## 📊 Logging

La bibliothèque utilise le module `logging` de Python. Les logs incluent :

- 🔐 Chiffrement en cours
- 🔓 Déchiffrement en cours
- 📁 Opérations sur les dossiers
- ✅ Opérations réussies
- ❌ Erreurs

**Format des logs :**
```
%(asctime)s - %(levelname)s - %(message)s
```

## 🔄 Migration

Si vous migrez d'une ancienne version :

1. Les fichiers sont maintenant dans `data/keys/` et `data/chunks/`
2. Les anciens dossiers `keys/` et `output/` ne sont plus utilisés
3. La structure des métadonnées JSON reste compatible

## 📄 Licence

Voir le fichier `LICENSE` à la racine du projet.

---

**Développé pour MeshDrive** 🔐

