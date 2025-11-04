# 🔐 MeshDrive - Datacenter Décentralisé

MeshDrive est un système de stockage sécurisé décentralisé qui permet de chiffrer, stocker et gérer des fichiers de manière sécurisée. Chaque utilisateur peut héberger son propre serveur pour stocker ses fichiers chiffrés.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [API Documentation](#-api-documentation)
- [Sécurité](#-sécurité)
- [Développement](#-développement)

## ✨ Fonctionnalités

### Gestion des fichiers
- ✅ **Chiffrement AES-256-GCM** : Chiffrement de bout en bout avec AES-256-GCM
- ✅ **Découpage en chunks** : Fichiers divisés en chunks de 1 Mo pour une gestion optimale
- ✅ **Upload/Download** : Upload et téléchargement de fichiers avec préservation du nom original
- ✅ **Suppression** : Suppression sécurisée des fichiers et de leurs chunks

### Gestion des dossiers
- ✅ **Structure hiérarchique** : Organisation des fichiers en dossiers et sous-dossiers
- ✅ **Création/Suppression** : Gestion complète des dossiers avec suppression récursive
- ✅ **Déplacement de fichiers** : Déplacement de fichiers entre dossiers
- ✅ **Téléchargement ZIP** : Téléchargement de dossiers complets en archive ZIP

### Interface Web
- ✅ **Interface moderne** : Interface web responsive avec thème sombre
- ✅ **Drag & Drop** : Upload de fichiers par glisser-déposer
- ✅ **Upload de dossiers** : Upload de plusieurs fichiers simultanément
- ✅ **Recherche et tri** : Recherche et tri des fichiers par nom, date ou taille
- ✅ **Sélection multiple** : Sélection multiple de fichiers pour actions en masse
- ✅ **Navigation** : Navigation avec historique (retour/avancer)
- ✅ **Breadcrumb** : Affichage du chemin actuel avec navigation

## 🏗️ Architecture

### Stack technique

```
┌─────────────────────────────────────────┐
│         Frontend (Web)                   │
│  - HTML/CSS/JavaScript (Vanilla)       │
│  - API REST (fetch)                     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Backend (FastAPI)                │
│  - FastAPI (Python 3.13+)               │
│  - CORS middleware                      │
│  - Static files serving                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Cryptolib (Library)             │
│  - Chiffrement AES-256-GCM              │
│  - Gestion des chunks                   │
│  - Gestion des métadonnées              │
│  - Gestion des dossiers                 │
└─────────────────────────────────────────┘
```

### Composants

1. **Frontend (`web/`)** : Interface utilisateur web moderne
2. **Backend (`api/`)** : API REST FastAPI
3. **Cryptolib (`cryptolib/`)** : Bibliothèque de chiffrement et gestion de fichiers
4. **P2P (`p2p/`)** : Scripts pour les échanges peer-to-peer (en développement)

## 🚀 Installation

### Prérequis

- Python 3.13 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
# Depuis la racine du projet
pip install fastapi uvicorn python-multipart cryptography
```

### Structure des dossiers

Le projet créera automatiquement les dossiers suivants :
- `keys/` : Métadonnées et clés de chiffrement (JSON)
- `output/` : Fichiers chiffrés (chunks .enc)

## 💻 Utilisation

### 1. Lancer l'API FastAPI

```bash
cd api
python run_api.py
```

L'API sera accessible sur `http://localhost:8000`

### 2. Accéder à l'interface web

Ouvrez votre navigateur et accédez à :
- **Interface web** : http://localhost:8000/web/
- **Documentation API** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### 3. Utilisation de l'interface

1. **Uploader un fichier** :
   - Cliquez sur "📤 Upload" ou glissez-déposez un fichier
   - Le fichier sera automatiquement chiffré et stocké

2. **Télécharger un fichier** :
   - Clic droit sur un fichier → "📥 Télécharger"
   - Ou sélectionnez plusieurs fichiers et cliquez sur "📥 Télécharger sélection"

3. **Créer un dossier** :
   - Cliquez sur "📁 Nouveau dossier"
   - Entrez le nom du dossier

4. **Déplacer un fichier** :
   - Clic droit sur un fichier → "📦 Déplacer"
   - Sélectionnez le dossier de destination

5. **Supprimer** :
   - Clic droit → "🗑️ Supprimer"
   - Ou sélectionnez plusieurs éléments et cliquez sur "🗑️ Supprimer la sélection"

## 📁 Structure du projet

```
MeshDrive/
├── api/                    # API FastAPI
│   ├── crypto_api.py       # Endpoints de l'API
│   ├── run_api.py          # Script de lancement
│   └── README.md           # Documentation API
│
├── cryptolib/              # Bibliothèque de chiffrement
│   ├── __init__.py         # Point d'entrée principal
│   ├── config.py           # Configuration
│   ├── models.py           # Modèles de données
│   ├── chunk_manager.py    # Gestion des chunks
│   ├── encryptor.py        # Chiffrement
│   ├── decryptor.py        # Déchiffrement
│   ├── metadata_manager.py # Gestion des métadonnées
│   └── folder_manager.py   # Gestion des dossiers
│
├── web/                    # Interface web
│   ├── index.html          # Page principale
│   ├── styles.css          # Styles CSS
│   ├── js/                 # Modules JavaScript
│   │   ├── api.js          # Client API JavaScript
│   │   ├── state.js        # État global
│   │   ├── utils.js        # Utilitaires
│   │   ├── navigation.js   # Navigation
│   │   ├── ui.js           # Interface utilisateur
│   │   ├── files.js        # Gestion des fichiers
│   │   ├── folders.js     # Gestion des dossiers
│   │   ├── dragdrop.js    # Drag & drop
│   │   └── main.js        # Point d'entrée
│   └── README.md           # Documentation web
│
├── p2p/                    # Peer-to-peer (en développement)
│   ├── listener.py
│   └── sender.py
│
├── keys/                   # Métadonnées (ignoré par git)
│   └── _folders/           # Métadonnées des dossiers
│
├── output/                 # Fichiers chiffrés (ignoré par git)
│
├── .gitignore              # Fichiers ignorés par git
└── README.md               # Ce fichier
```

## 📚 API Documentation

### Endpoints principaux

#### Fichiers

- `POST /encrypt` : Chiffrer un fichier
- `GET /decrypt/{file_id}` : Déchiffrer un fichier
- `GET /files` : Lister les fichiers
- `GET /files/{file_id}` : Informations d'un fichier
- `PUT /files/{file_id}/move` : Déplacer un fichier
- `DELETE /files/{file_id}` : Supprimer un fichier

#### Dossiers

- `POST /folders` : Créer un dossier
- `GET /folders` : Lister les dossiers
- `GET /folders-all` : Lister tous les dossiers
- `GET /folders/{folder_path}` : Informations d'un dossier
- `DELETE /folders/{folder_path}` : Supprimer un dossier
- `GET /folder-contents` : Contenu d'un dossier
- `GET /download-folder/{folder_path}` : Télécharger un dossier en ZIP
- `POST /encrypt-folder` : Uploader plusieurs fichiers

#### Autres

- `GET /` : Informations sur l'API
- `GET /health` : État de l'API

Pour la documentation complète, consultez :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Exemple d'utilisation avec curl

```bash
# Chiffrer un fichier
curl -X POST "http://localhost:8000/encrypt" \
  -F "file=@mon_fichier.pdf" \
  -F "folder_path=/"

# Lister les fichiers
curl "http://localhost:8000/files?folder_path=/"

# Déchiffrer un fichier
curl "http://localhost:8000/decrypt/{file_id}?download=true" \
  --output fichier_dechiffre.pdf

# Créer un dossier
curl -X POST "http://localhost:8000/folders" \
  -H "Content-Type: application/json" \
  -d '{"folder_name": "MonDossier", "parent_path": "/"}'
```

## 🔒 Sécurité

### Chiffrement

- **Algorithme** : AES-256-GCM (Advanced Encryption Standard en mode GCM)
- **Taille de clé** : 256 bits
- **Taille de nonce** : 96 bits
- **Taille des chunks** : 1 Mo par défaut

### Stockage

- **Clés de chiffrement** : Stockées dans `keys/` (JSON)
- **Fichiers chiffrés** : Stockés dans `output/` (chunks .enc)
- **Métadonnées** : Stockées dans `keys/` (JSON)

⚠️ **Important** : Les fichiers `keys/` et `output/` ne doivent **jamais** être committés sur Git. Ils sont automatiquement ignorés par `.gitignore`.

### Bonnes pratiques

1. Ne partagez jamais vos clés de chiffrement
2. Sauvegardez régulièrement le dossier `keys/`
3. Utilisez HTTPS en production
4. Configurez CORS correctement pour la production

## 🛠️ Développement

### Modifier la configuration

Éditez `cryptolib/config.py` pour modifier :
- Taille des chunks (`CHUNK_SIZE`)
- Répertoires de stockage (`KEYS_DIR`, `CHUNKS_DIR`)
- Niveau de logging (`LOG_LEVEL`)

### Ajouter de nouvelles fonctionnalités

1. **Backend** : Ajoutez les endpoints dans `api/crypto_api.py`
2. **Frontend** : Ajoutez les fonctions dans `web/js/` et `web/api.js`
3. **Cryptolib** : Ajoutez la logique métier dans `cryptolib/`

### Tests

Un script de test est disponible dans `api/test_crypto_api.py` :

```bash
cd api
python test_crypto_api.py
```

### Logs

Les logs sont affichés dans la console avec des emojis pour faciliter la lecture :
- 🔐 Chiffrement
- 🔓 Déchiffrement
- 📁 Dossiers
- 🗑️ Suppression
- ✅ Succès
- ❌ Erreur

## 📝 Notes

- Les fichiers sont automatiquement chiffrés lors de l'upload
- Les noms de fichiers originaux sont préservés
- La suppression d'un dossier supprime récursivement tous ses fichiers et sous-dossiers
- L'historique de navigation permet de naviguer entre les dossiers visités

## 🤝 Contribution

Ce projet est en développement actif. Les contributions sont les bienvenues !

## 📄 Licence

Voir le fichier `LICENSE` pour plus d'informations.

---

**Développé avec ❤️ pour un stockage sécurisé et décentralisé**
