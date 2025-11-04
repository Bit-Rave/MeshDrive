# Interface Web MeshDrive

Interface web pour utiliser l'API FastAPI de MeshDrive Crypto.

## Fonctionnalités

- ✅ Liste des fichiers chiffrés
- ✅ Upload et chiffrement de fichiers
- ✅ Téléchargement et déchiffrement de fichiers
- ✅ Suppression de fichiers
- ✅ Recherche et tri des fichiers
- ✅ Affichage des détails des fichiers

## Utilisation

### 1. Lancer l'API FastAPI

Depuis le dossier `api/` :
```bash
cd api
python run_api.py
```

Ou directement avec uvicorn :
```bash
cd api
uvicorn crypto_api:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur `http://localhost:8000`

### 2. Accéder à l'interface web

L'interface web est accessible via l'API :
- **Interface web** : http://localhost:8000/web/
- **Documentation API** : http://localhost:8000/docs

### 3. Utilisation de l'interface

1. **Uploader un fichier** : Cliquez sur le bouton "📤 Upload" et sélectionnez un fichier
2. **Télécharger un fichier** : Clic droit sur un fichier → "📥 Télécharger"
3. **Supprimer un fichier** : Clic droit sur un fichier → "🗑️ Supprimer"
4. **Voir les détails** : Double-clic ou clic droit → "📋 Détails"

## Configuration

L'URL de l'API est définie dans `js/api.js` :

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

Si vous changez le port de l'API, modifiez cette constante.

## Fichiers

- `index.html` : Interface utilisateur principale
- `styles.css` : Styles CSS
- `js/` : Modules JavaScript
  - `api.js` : Module JavaScript pour les appels API
  - `state.js` : État global de l'application
  - `utils.js` : Fonctions utilitaires
  - `navigation.js` : Gestion de la navigation
  - `ui.js` : Interface utilisateur (modales, menus contextuels)
  - `files.js` : Gestion des fichiers
  - `folders.js` : Gestion des dossiers
  - `dragdrop.js` : Fonctionnalité drag & drop
  - `main.js` : Point d'entrée de l'application
- `README.md` : Ce fichier

## Notes

- L'interface nécessite que l'API FastAPI soit en cours d'exécution
- Les fichiers sont chiffrés côté serveur avec AES-256-GCM
- Les fichiers chiffrés sont stockés dans `output/`
- Les métadonnées sont stockées dans `keys/`

