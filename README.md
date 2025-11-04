language utilisée pour le backend : `python3 version 3.13.9`

`docker` pour le déploiement 

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
