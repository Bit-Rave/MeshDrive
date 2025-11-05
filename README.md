# 🔐 MeshDrive - Datacenter Décentralisé Zero-Knowledge

MeshDrive est un système de stockage cloud sécurisé avec chiffrement end-to-end (E2EE) et architecture Zero-Knowledge. Il permet aux utilisateurs de stocker leurs fichiers de manière chiffrée sur un serveur décentralisé, avec isolation complète des données par utilisateur.

## 🎯 Fonctionnalités principales

- ✅ **Chiffrement Zero-Knowledge** : Chiffrement côté client avec Web Crypto API
- ✅ **Multi-utilisateurs** : Isolation complète des données par utilisateur
- ✅ **Authentification JWT** : Système d'authentification sécurisé
- ✅ **Interface web moderne** : Interface utilisateur complète avec drag & drop
- ✅ **API REST** : API complète pour l'intégration
- ✅ **Gestion des dossiers** : Organisation hiérarchique des fichiers
- ✅ **Quotas par utilisateur** : Limitation de stockage configurable
- ✅ **Audit logging** : Traçabilité complète des actions
- ✅ **Validation et sécurité** : Protection contre path traversal, injection, etc.

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **API modulaire** : Routes, services, dépendances séparés
- **Chiffrement AES-256-GCM** : Chiffrement robuste des fichiers
- **Base de données SQLite** : Stockage des utilisateurs et métadonnées
- **Isolation par utilisateur** : Chaque utilisateur a son propre espace de stockage

### Frontend (Vanilla JavaScript)
- **Modules JavaScript** : Architecture modulaire et maintenable
- **Chiffrement côté client** : Zero-Knowledge avec Web Crypto API
- **Interface responsive** : Compatible desktop et mobile

### Cryptographie
- **AES-256-GCM** : Chiffrement symétrique robuste
- **PBKDF2** : Dérivation de clés depuis les mots de passe (100,000 itérations)
- **Fernet** : Chiffrement des clés avec mot de passe utilisateur
- **Chunks** : Découpage des fichiers en morceaux de 1MB

## 🚀 Installation

### Prérequis
- Python 3.13.9 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancement de l'API

```bash
python api/run_api.py
```

L'API sera accessible sur `http://127.0.0.1:8000`

### Accès à l'interface web

- **Dashboard** : http://127.0.0.1:8000/
- **Drive** : http://127.0.0.1:8000/drive
- **Login** : http://127.0.0.1:8000/login.html
- **Documentation API** : http://127.0.0.1:8000/docs

## 📁 Structure du projet

```
MeshDrive/
├── api/                    # API FastAPI (backend)
│   ├── app.py             # Point d'entrée principal
│   ├── routes/            # Routes modulaires
│   ├── services/          # Services métier
│   ├── dependencies/      # Dépendances FastAPI
│   └── utils/             # Utilitaires API
├── core/                   # Modules core
│   ├── database.py        # Modèles SQLAlchemy
│   ├── auth.py            # Authentification JWT
│   ├── auth_routes.py     # Routes d'authentification
│   └── security/          # Modules de sécurité
├── cryptolib/              # Bibliothèque de chiffrement
│   ├── encryptor.py       # Chiffrement de fichiers
│   ├── decryptor.py       # Déchiffrement de fichiers
│   ├── chunk_manager.py   # Gestion des chunks
│   ├── metadata_manager.py # Gestion des métadonnées
│   └── key_encryption.py  # Chiffrement des clés
├── web/                   # Interface web (frontend)
│   ├── dashboard.html      # Page principale
│   ├── drive.html          # Interface du drive
│   ├── login.html          # Page de connexion
│   └── js/                 # Modules JavaScript
└── data/                  # Données stockées
    ├── users/             # Données par utilisateur
    ├── logs/              # Logs d'audit
    └── meshdrive.db       # Base de données SQLite
```

## 🔒 Sécurité

MeshDrive implémente une architecture **Zero-Knowledge** où :
- ✅ Les fichiers sont chiffrés **côté client** avant l'upload
- ✅ Les clés de chiffrement sont chiffrées avec le **mot de passe utilisateur**
- ✅ Le serveur ne peut jamais déchiffrer les fichiers
- ✅ Les métadonnées (noms de fichiers) sont chiffrées
- ✅ Vérification d'intégrité des données

Voir `SECURITY.md` pour plus de détails sur les mesures de sécurité.

## 📚 Documentation

- **API** : Voir `api/README.md`
- **Cryptolib** : Voir `cryptolib/README.md`
- **Interface Web** : Voir `web/README.md`
- **Sécurité** : Voir `SECURITY.md`
- **Documentation IA** : Voir `ia.txt`

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework web async
- **SQLAlchemy** : ORM pour la base de données
- **SQLite** : Base de données
- **JWT (python-jose)** : Authentification par tokens
- **bcrypt** : Hashage des mots de passe
- **cryptography** : Bibliothèque de chiffrement

### Frontend
- **Vanilla JavaScript** : Pas de framework
- **Web Crypto API** : Chiffrement côté client
- **Fetch API** : Appels HTTP
- **HTML5/CSS** : Interface utilisateur

## 📝 Licence

Voir `LICENSE` pour plus d'informations.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📞 Support

Pour toute question ou problème, consultez la documentation ou ouvrez une issue sur le dépôt du projet.

---

**Version** : 2.0.0  
**Dernière mise à jour** : Janvier 2025  
**Statut** : En développement actif
