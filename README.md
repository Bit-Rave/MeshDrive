## 💻 Développement
---

### 🧩 **Structure du projet**

- **Frontend**  
  - **Technologies** : HTML / CSS / JavaScript  
  - **Dossier** : `web/`  
  - Contient l’interface utilisateur (pages web, scripts et styles).  

- **Backend**  
  - **Framework** : [FastAPI](https://fastapi.tiangolo.com/)  
  - Gère la logique métier, les requêtes et les API endpoints.  
  - Développé avec **Python 3.13.9**.  

- **Chiffrement**  
  - **Dossier principal** : `cryptolib/`  
    - Contient les **scripts Python** dédiés aux opérations de chiffrement et déchiffrement.  
  - **Dossier des clés** : `keys/`  
    - Contient des **fichiers JSON** stockant les **métadonnées** et **informations sur les fichiers uploadés**, notamment ceux **divisés en plusieurs parties** (*chunks*).  

- **Tests Peer-to-Peer (P2P)**  
  - **Dossier** : `p2p/`  
  - Contient les **scripts et outils de test** pour les échanges de fichiers entre pairs.  

- **Fichiers chiffrés**  
  - **Dossier** : `output/`  
  - Contient les **chunks chiffrés** des fichiers uploadés.  

---

### 🐳 **Déploiement**

- Le projet est **conteneurisé avec Docker** pour simplifier le déploiement et assurer la reproductibilité de l’environnement.  
- Le fichier `Dockerfile` et éventuellement `docker-compose.yml` définissent la configuration du backend, du frontend et des dépendances nécessaires.  
- Commandes principales :
  ```bash
  docker build -t nom_du_projet .
  docker run -d -p 8000:8000 nom_du_projet
  ```
### ⚙️ Environnement technique
- Langage principal : Python 3.13.9
- Framework backend : FastAPI
- Conteneurisation : Docker
- Frontend : HTML / CSS / JavaScript