# 🖥️ MeshDrive Host CLI

Interface en ligne de commande pour gérer le serveur MeshDrive (host).

## 📋 Prérequis

- Python 3.8+
- Les dépendances du projet (voir `requirements.txt` à la racine)
- Typer (pour l'interface CLI)

## 🚀 Installation

1. Assurez-vous d'être dans le répertoire du projet :
```bash
cd MeshDrive
```

2. Installez les dépendances si nécessaire :
```bash
pip install typer
```

3. Rendez le script exécutable (Linux/Mac) :
```bash
chmod +x host/cli.py
```

## 🧪 Mode Test

Pour tester le script sans affecter vos données de production, utilisez le flag `--test` :

**Mode test utilise :**
- Dossiers séparés : `test_keys/` et `test_output/` (au lieu de `keys/` et `output/`)
- Port différent : `8001` (au lieu de `8000`)
- Configuration séparée : `host_config.test.json`
- Logs séparés : `host.test.log`
- PID séparé : `.server.test.pid`

**Exemples :**
```bash
# Démarrer en mode test
python host/cli.py start --test

# Voir le statut en mode test
python host/cli.py status --test

# Voir les stats en mode test
python host/cli.py stats --test

# Arrêter le serveur en mode test
python host/cli.py stop --test

# Voir les logs en mode test
python host/cli.py logs --test
```

⚠️ **Important** : Les données de test sont complètement isolées des données de production. Vous pouvez supprimer les dossiers `test_keys/` et `test_output/` à tout moment sans risque.

## 🎯 Initialisation

La première fois, initialisez la configuration :

```bash
python host/cli.py init
```

Ou avec l'alias (si configuré) :
```bash
meshdrive-host init
```

## 📚 Commandes disponibles

### 🚀 `start` - Démarrer le serveur

Démarre le serveur MeshDrive.

```bash
python host/cli.py start
```

**Options :**
- `--host`, `-h` : Adresse IP du serveur (défaut: 0.0.0.0)
- `--port`, `-p` : Port du serveur (défaut: 8000)
- `--reload` / `--no-reload` : Mode rechargement automatique (défaut: activé)
- `--background`, `-b` : Démarrer en arrière-plan

**Exemples :**
```bash
# Démarrer sur le port 8080
python host/cli.py start --port 8080

# Démarrer en arrière-plan
python host/cli.py start --background

# Démarrer sans rechargement automatique
python host/cli.py start --no-reload
```

### 🛑 `stop` - Arrêter le serveur

Arrête le serveur en cours d'exécution.

```bash
python host/cli.py stop
```

### 📊 `status` - État du serveur

Affiche l'état actuel du serveur (en cours d'exécution ou arrêté).

```bash
python host/cli.py status
```

### 📈 `stats` - Statistiques du stockage

Affiche les statistiques du stockage :
- Nombre de fichiers
- Nombre de chunks
- Nombre de dossiers
- Espace utilisé

```bash
python host/cli.py stats
```

**Exemple de sortie :**
```
📈 Statistiques du stockage MeshDrive

📁 Dossier clés: /path/to/keys
   Fichiers: 10
   Taille: 2.45 MB
   Dossiers: 3

📦 Dossier chunks: /path/to/output
   Chunks: 25
   Taille: 45.67 MB

💾 Total:
   Taille totale: 48.12 MB
   Fichiers: 10
   Chunks: 25
```

### ⚙️ `config` - Gestion de la configuration

Gère la configuration du serveur.

**Afficher toute la configuration :**
```bash
python host/cli.py config --list
```

**Afficher une valeur spécifique :**
```bash
python host/cli.py config host
python host/cli.py config port
```

**Modifier une valeur :**
```bash
python host/cli.py config port 8080
python host/cli.py config reload false
```

**Clés de configuration disponibles :**
- `host` : Adresse IP du serveur
- `port` : Port du serveur
- `keys_dir` : Dossier des clés de chiffrement
- `chunks_dir` : Dossier des chunks chiffrés
- `chunk_size` : Taille des chunks en bytes
- `reload` : Mode rechargement automatique (true/false)
- `log_level` : Niveau de log (info, debug, warning, error)

### 📝 `logs` - Afficher les logs

Affiche les logs du serveur.

```bash
# Afficher les 50 dernières lignes
python host/cli.py logs

# Afficher les 100 dernières lignes
python host/cli.py logs --lines 100

# Suivre les logs en temps réel
python host/cli.py logs --follow
```

### 🧹 `clean` - Nettoyer les fichiers orphelins

Supprime les chunks chiffrés qui n'ont plus de métadonnées associées (fichiers orphelins).

```bash
# Mode interactif
python host/cli.py clean

# Mode automatique (sans confirmation)
python host/cli.py clean --yes
```

### 🧹 `clean-test` - Nettoyer les données de test

Supprime toutes les données de test (`test_keys/`, `test_output/`, config, logs). Utile pour réinitialiser complètement l'environnement de test.

```bash
# Mode interactif
python host/cli.py clean-test

# Mode automatique (sans confirmation)
python host/cli.py clean-test --yes
```

### 🎯 `init` - Initialiser la configuration

Initialise la configuration du host. Utile pour la première utilisation.

```bash
python host/cli.py init
```

## 🔧 Configuration

La configuration est stockée dans `host/host_config.json`. Vous pouvez la modifier manuellement ou via la commande `config`.

**Exemple de configuration :**
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "keys_dir": "/path/to/keys",
  "chunks_dir": "/path/to/output",
  "chunk_size": 1048576,
  "reload": true,
  "log_level": "info"
}
```

## 📁 Structure des fichiers

```
host/
├── cli.py              # Script CLI principal
├── host_config.json    # Configuration du host (généré)
├── .server.pid         # PID du serveur en arrière-plan (généré)
├── host.log            # Logs du serveur (généré)
└── README.md           # Ce fichier
```

## 🌐 Accès à l'interface web

Une fois le serveur démarré, accédez à l'interface web via :

```
http://localhost:8000/web
```

Ou avec l'adresse configurée :

```
http://<host>:<port>/web
```

## 💡 Astuces

### Alias pour faciliter l'utilisation

Vous pouvez créer un alias pour faciliter l'utilisation :

**Linux/Mac (bash/zsh) :**
```bash
alias meshdrive-host='python /path/to/MeshDrive/host/cli.py'
```

**Windows (PowerShell) :**
```powershell
function meshdrive-host { python C:\path\to\MeshDrive\host\cli.py $args }
```

Ensuite, vous pouvez utiliser :
```bash
meshdrive-host start
meshdrive-host status
meshdrive-host stats
```

### Démarrer automatiquement au démarrage

Vous pouvez configurer le serveur pour qu'il démarre automatiquement au démarrage du système :

**Linux (systemd) :**
Créez un service systemd dans `/etc/systemd/system/meshdrive.service` :

```ini
[Unit]
Description=MeshDrive Host Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/MeshDrive
ExecStart=/usr/bin/python3 /path/to/MeshDrive/host/cli.py start --background
Restart=always

[Install]
WantedBy=multi-user.target
```

Puis activez-le :
```bash
sudo systemctl enable meshdrive
sudo systemctl start meshdrive
```

## 🐛 Dépannage

### Le serveur ne démarre pas

1. Vérifiez que le port n'est pas déjà utilisé :
```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

2. Vérifiez les logs :
```bash
python host/cli.py logs
```

### Le serveur ne s'arrête pas

Si `stop` ne fonctionne pas, vous pouvez forcer l'arrêt :

```bash
# Trouver le PID
python host/cli.py status

# Arrêter manuellement (remplacez PID par le numéro réel)
kill PID
```

### Les fichiers orphelins

Si vous avez des chunks sans métadonnées, utilisez :
```bash
python host/cli.py clean
```

## 📞 Support

Pour plus d'informations, consultez le README principal du projet ou les issues GitHub.

