#!/usr/bin/env python3
"""
Script CLI pour gérer le serveur MeshDrive (Host)
"""

import typer
import json
import sys
import subprocess
import signal
import os
import time
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil

# Ajouter le répertoire parent au path pour importer cryptolib
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptolib import CryptoSystem
from cryptolib.config import KEYS_DIR, CHUNKS_DIR

app = typer.Typer(help="🔐 MeshDrive Host CLI - Gestion du serveur de stockage")

# Obtenir le répertoire du projet (parent de host/)
PROJECT_ROOT = Path(__file__).parent.parent

# Variables globales pour le mode test
TEST_MODE = False

# Configuration par défaut
def get_config_file():
    """Retourne le chemin du fichier de configuration selon le mode"""
    if TEST_MODE:
        return Path(__file__).parent / "host_config.test.json"
    return Path(__file__).parent / "host_config.json"

CONFIG_FILE = get_config_file()
PID_FILE = Path(__file__).parent / (".server.test.pid" if TEST_MODE else ".server.pid")
LOG_FILE = Path(__file__).parent / ("host.test.log" if TEST_MODE else "host.log")

# Configuration par défaut
def get_default_config():
    """Retourne la configuration par défaut selon le mode"""
    if TEST_MODE:
        return {
            "host": "0.0.0.0",
            "port": 8001,  # Port différent pour les tests
            "keys_dir": str((PROJECT_ROOT / "test_keys").absolute()),
            "chunks_dir": str((PROJECT_ROOT / "test_output").absolute()),
            "chunk_size": 1024 * 1024,  # 1 MB
            "reload": True,
            "log_level": "info"
        }
    return {
        "host": "0.0.0.0",
        "port": 8000,
        "keys_dir": str((PROJECT_ROOT / "keys").absolute()),
        "chunks_dir": str((PROJECT_ROOT / "output").absolute()),
        "chunk_size": 1024 * 1024,  # 1 MB
        "reload": True,
        "log_level": "info"
    }

DEFAULT_CONFIG = get_default_config()


def load_config():
    """Charge la configuration depuis le fichier"""
    config_file = get_config_file()
    default_config = get_default_config()
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Fusionner avec les valeurs par défaut
                final_config = default_config.copy()
                final_config.update(config)
                return final_config
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de la config: {e}")
            return default_config
    return default_config.copy()


def save_config(config: dict):
    """Sauvegarde la configuration dans le fichier"""
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ Configuration sauvegardée dans {config_file}")


def get_server_pid():
    """Récupère le PID du serveur s'il est en cours d'exécution"""
    pid_file = Path(__file__).parent / (".server.test.pid" if TEST_MODE else ".server.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                # Vérifier si le processus existe toujours
                try:
                    os.kill(pid, 0)  # Vérifie si le processus existe
                    return pid
                except OSError:
                    # Le processus n'existe plus
                    pid_file.unlink()
                    return None
        except Exception:
            return None
    return None


def format_size(size_bytes: int) -> str:
    """Formate une taille en bytes en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_storage_stats():
    """Calcule les statistiques du stockage"""
    config = load_config()
    keys_dir = Path(config["keys_dir"])
    chunks_dir = Path(config["chunks_dir"])
    
    stats = {
        "keys_dir": str(keys_dir),
        "chunks_dir": str(chunks_dir),
        "keys_size": 0,
        "chunks_size": 0,
        "total_size": 0,
        "files_count": 0,
        "chunks_count": 0,
        "folders_count": 0
    }
    
    # Taille et nombre de fichiers dans keys/
    if keys_dir.exists():
        for file_path in keys_dir.rglob("*.json"):
            if file_path.is_file():
                stats["files_count"] += 1
                stats["keys_size"] += file_path.stat().st_size
        
        # Compter les dossiers
        folders_dir = keys_dir / "_folders"
        if folders_dir.exists():
            for folder_file in folders_dir.glob("*.json"):
                if folder_file.is_file():
                    stats["folders_count"] += 1
    
    # Taille et nombre de chunks dans output/
    if chunks_dir.exists():
        for chunk_file in chunks_dir.rglob("*.enc"):
            if chunk_file.is_file():
                stats["chunks_count"] += 1
                stats["chunks_size"] += chunk_file.stat().st_size
    
    stats["total_size"] = stats["keys_size"] + stats["chunks_size"]
    return stats


@app.command()
def start(
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Adresse IP du serveur"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port du serveur"),
    reload: Optional[bool] = typer.Option(None, "--reload/--no-reload", help="Mode rechargement automatique"),
    background: bool = typer.Option(False, "--background", "-b", help="Démarrer en arrière-plan"),
    test: bool = typer.Option(False, "--test", help="Mode test (utilise test_keys/ et test_output/, port 8001)")
):
    """🚀 Démarre le serveur MeshDrive"""
    global TEST_MODE
    if test:
        TEST_MODE = True
    
    pid = get_server_pid()
    if pid:
        mode = "TEST" if TEST_MODE else "PRODUCTION"
        print(f"⚠️  Le serveur ({mode}) est déjà en cours d'exécution (PID: {pid})")
        print("   Utilisez 'meshdrive-host stop' pour l'arrêter")
        raise typer.Exit(1)
    
    config = load_config()
    
    # Appliquer les paramètres en ligne de commande
    if host:
        config["host"] = host
    if port:
        config["port"] = port
    if reload is not None:
        config["reload"] = reload
    
    save_config(config)
    
    # Vérifier que les répertoires existent
    keys_dir = Path(config["keys_dir"])
    chunks_dir = Path(config["chunks_dir"])
    keys_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    mode_str = "🧪 TEST" if TEST_MODE else "🚀 PRODUCTION"
    print(f"{mode_str} - Démarrage du serveur MeshDrive...")
    print(f"   📍 Adresse: {config['host']}:{config['port']}")
    print(f"   📁 Clés: {keys_dir}")
    print(f"   📦 Chunks: {chunks_dir}")
    
    # Préparer la commande uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.crypto_api:app",
        "--host", config["host"],
        "--port", str(config["port"]),
        "--log-level", config["log_level"]
    ]
    
    if config["reload"]:
        cmd.append("--reload")
    
    log_file_path = Path(__file__).parent / ("host.test.log" if TEST_MODE else "host.log")
    pid_file_path = Path(__file__).parent / (".server.test.pid" if TEST_MODE else ".server.pid")
    
    if background:
        # Démarrer en arrière-plan
        with open(log_file_path, 'a') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT
            )
        
        # Sauvegarder le PID
        with open(pid_file_path, 'w') as f:
            f.write(str(process.pid))
        
        print(f"✅ Serveur démarré en arrière-plan (PID: {process.pid})")
        print(f"   📝 Logs: {log_file_path}")
        print(f"   🌐 Interface web: http://{config['host']}:{config['port']}/web")
    else:
        # Démarrer au premier plan
        try:
            subprocess.run(cmd, cwd=PROJECT_ROOT)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")


@app.command()
def stop(
    test: bool = typer.Option(False, "--test", help="Arrêter le serveur en mode test")
):
    """🛑 Arrête le serveur MeshDrive"""
    global TEST_MODE
    if test:
        TEST_MODE = True
    
    pid = get_server_pid()
    if not pid:
        print("ℹ️  Aucun serveur en cours d'exécution")
        raise typer.Exit(0)
    
    try:
        mode_str = "TEST" if TEST_MODE else "PRODUCTION"
        print(f"🛑 Arrêt du serveur {mode_str} (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Attendre un peu pour que le processus se termine proprement
        time.sleep(2)
        
        # Vérifier si le processus existe encore
        try:
            os.kill(pid, 0)
            # Si on arrive ici, le processus existe encore, on force l'arrêt
            print("⚠️  Le serveur ne répond pas, arrêt forcé...")
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # Le processus s'est arrêté
        
        pid_file_path = Path(__file__).parent / (".server.test.pid" if TEST_MODE else ".server.pid")
        pid_file_path.unlink()
        print("✅ Serveur arrêté")
    except ProcessLookupError:
        print("⚠️  Le processus n'existe plus")
        pid_file_path = Path(__file__).parent / (".server.test.pid" if TEST_MODE else ".server.pid")
        pid_file_path.unlink()
    except Exception as e:
        print(f"❌ Erreur lors de l'arrêt: {e}")
        raise typer.Exit(1)


@app.command()
def status(
    test: bool = typer.Option(False, "--test", help="Afficher le statut du serveur en mode test")
):
    """📊 Affiche l'état du serveur"""
    global TEST_MODE
    if test:
        TEST_MODE = True
    
    pid = get_server_pid()
    config = load_config()
    
    mode_str = "🧪 TEST" if TEST_MODE else "🚀 PRODUCTION"
    print(f"📊 État du serveur MeshDrive ({mode_str})\n")
    
    if pid:
        print(f"🟢 Statut: En cours d'exécution")
        print(f"   PID: {pid}")
        print(f"   📍 Adresse: {config['host']}:{config['port']}")
        print(f"   🌐 Interface web: http://{config['host']}:{config['port']}/web")
    else:
        print("🔴 Statut: Arrêté")
    
    print(f"\n⚙️  Configuration:")
    print(f"   📁 Dossier clés: {config['keys_dir']}")
    print(f"   📦 Dossier chunks: {config['chunks_dir']}")
    print(f"   📏 Taille chunk: {format_size(config['chunk_size'])}")
    print(f"   🔄 Rechargement: {'Activé' if config['reload'] else 'Désactivé'}")


@app.command()
def stats(
    test: bool = typer.Option(False, "--test", help="Afficher les statistiques du mode test")
):
    """📈 Affiche les statistiques du stockage"""
    global TEST_MODE
    if test:
        TEST_MODE = True
    
    mode_str = "🧪 TEST" if TEST_MODE else "🚀 PRODUCTION"
    print(f"📈 Statistiques du stockage MeshDrive ({mode_str})\n")
    
    stats = get_storage_stats()
    
    print(f"📁 Dossier clés: {stats['keys_dir']}")
    print(f"   Fichiers: {stats['files_count']}")
    print(f"   Taille: {format_size(stats['keys_size'])}")
    print(f"   Dossiers: {stats['folders_count']}")
    
    print(f"\n📦 Dossier chunks: {stats['chunks_dir']}")
    print(f"   Chunks: {stats['chunks_count']}")
    print(f"   Taille: {format_size(stats['chunks_size'])}")
    
    print(f"\n💾 Total:")
    print(f"   Taille totale: {format_size(stats['total_size'])}")
    print(f"   Fichiers: {stats['files_count']}")
    print(f"   Chunks: {stats['chunks_count']}")


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Clé de configuration à modifier"),
    value: Optional[str] = typer.Argument(None, help="Valeur à définir"),
    list_all: bool = typer.Option(False, "--list", "-l", help="Afficher toute la configuration")
):
    """⚙️  Gère la configuration du serveur"""
    config = load_config()
    
    if list_all:
        print("⚙️  Configuration actuelle:\n")
        for k, v in config.items():
            print(f"   {k}: {v}")
        return
    
    if key is None:
        # Afficher toute la configuration
        print("⚙️  Configuration actuelle:\n")
        for k, v in config.items():
            print(f"   {k}: {v}")
        print("\n💡 Utilisez 'meshdrive-host config <key> <value>' pour modifier une valeur")
        return
    
    if value is None:
        # Afficher la valeur d'une clé
        if key in config:
            print(f"{key}: {config[key]}")
        else:
            print(f"❌ Clé '{key}' introuvable")
            print(f"   Clés disponibles: {', '.join(config.keys())}")
            raise typer.Exit(1)
    else:
        # Modifier une valeur
        if key not in config:
            print(f"❌ Clé '{key}' introuvable")
            print(f"   Clés disponibles: {', '.join(config.keys())}")
            raise typer.Exit(1)
        
        # Convertir la valeur selon le type attendu
        old_value = config[key]
        if isinstance(old_value, bool):
            new_value = value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(old_value, int):
            try:
                new_value = int(value)
            except ValueError:
                print(f"❌ La valeur doit être un entier pour la clé '{key}'")
                raise typer.Exit(1)
        else:
            new_value = value
        
        config[key] = new_value
        save_config(config)
        print(f"✅ {key}: {old_value} → {new_value}")


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Nombre de lignes à afficher"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Suivre les logs en temps réel"),
    test: bool = typer.Option(False, "--test", help="Afficher les logs du mode test")
):
    """📝 Affiche les logs du serveur"""
    global TEST_MODE
    if test:
        TEST_MODE = True
    
    log_file_path = Path(__file__).parent / ("host.test.log" if TEST_MODE else "host.log")
    
    if not log_file_path.exists():
        print("ℹ️  Aucun fichier de log trouvé")
        return
    
    if follow:
        # Suivre les logs en temps réel (comme tail -f)
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Lire les dernières lignes
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.rstrip())
                
                # Attendre les nouvelles lignes
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt de la surveillance des logs")
    else:
        # Afficher les dernières lignes
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())


@app.command()
def clean(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirmer sans demander")
):
    """🧹 Nettoie les fichiers orphelins (chunks sans métadonnées)"""
    config = load_config()
    keys_dir = Path(config["keys_dir"])
    chunks_dir = Path(config["chunks_dir"])
    
    if not confirm:
        response = typer.confirm("⚠️  Êtes-vous sûr de vouloir nettoyer les fichiers orphelins?")
        if not response:
            print("❌ Opération annulée")
            return
    
    print("🧹 Nettoyage des fichiers orphelins...\n")
    
    # Récupérer tous les file_ids des métadonnées
    valid_file_ids = set()
    if keys_dir.exists():
        for metadata_file in keys_dir.glob("*.json"):
            if metadata_file.stem != "_folders":
                valid_file_ids.add(metadata_file.stem)
    
    # Parcourir les chunks et vérifier s'ils ont une métadonnée
    orphaned_chunks = []
    if chunks_dir.exists():
        for chunk_file in chunks_dir.glob("*.enc"):
            # Extraire le file_id du nom du chunk (format: file_id_chunk_XXXX.enc)
            parts = chunk_file.stem.split("_chunk_")
            if len(parts) == 2:
                file_id = parts[0]
                if file_id not in valid_file_ids:
                    orphaned_chunks.append(chunk_file)
    
    if not orphaned_chunks:
        print("✅ Aucun fichier orphelin trouvé")
        return
    
    print(f"📦 {len(orphaned_chunks)} chunks orphelins trouvés")
    
    total_size = sum(chunk.stat().st_size for chunk in orphaned_chunks)
    print(f"💾 Taille totale: {format_size(total_size)}\n")
    
    if not confirm:
        response = typer.confirm(f"🗑️  Supprimer {len(orphaned_chunks)} chunks orphelins?")
        if not response:
            print("❌ Opération annulée")
            return
    
    # Supprimer les chunks orphelins
    deleted_count = 0
    deleted_size = 0
    for chunk in orphaned_chunks:
        try:
            size = chunk.stat().st_size
            chunk.unlink()
            deleted_count += 1
            deleted_size += size
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression de {chunk.name}: {e}")
    
    print(f"\n✅ {deleted_count} chunks supprimés")
    print(f"💾 Espace libéré: {format_size(deleted_size)}")


@app.command()
def clean_test(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirmer sans demander")
):
    """🧹 Nettoie les données de test (test_keys/ et test_output/)"""
    test_keys_dir = PROJECT_ROOT / "test_keys"
    test_output_dir = PROJECT_ROOT / "test_output"
    test_config_file = Path(__file__).parent / "host_config.test.json"
    test_log_file = Path(__file__).parent / "host.test.log"
    test_pid_file = Path(__file__).parent / ".server.test.pid"
    
    has_data = (test_keys_dir.exists() and any(test_keys_dir.iterdir())) or \
               (test_output_dir.exists() and any(test_output_dir.iterdir()))
    
    if not has_data:
        print("ℹ️  Aucune donnée de test trouvée")
        return
    
    if not confirm:
        response = typer.confirm("⚠️  Supprimer toutes les données de test? (test_keys/, test_output/, config, logs)")
        if not response:
            print("❌ Opération annulée")
            return
    
    print("🧹 Nettoyage des données de test...\n")
    
    deleted_count = 0
    
    # Supprimer les dossiers de test
    if test_keys_dir.exists():
        try:
            shutil.rmtree(test_keys_dir)
            print(f"✅ Supprimé: {test_keys_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression de {test_keys_dir}: {e}")
    
    if test_output_dir.exists():
        try:
            shutil.rmtree(test_output_dir)
            print(f"✅ Supprimé: {test_output_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression de {test_output_dir}: {e}")
    
    # Supprimer les fichiers de configuration/test
    for file_path in [test_config_file, test_log_file, test_pid_file]:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Supprimé: {file_path.name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Erreur lors de la suppression de {file_path}: {e}")
    
    print(f"\n✅ Nettoyage terminé ({deleted_count} éléments supprimés)")


@app.command()
def init():
    """🎯 Initialise la configuration du host"""
    config_file = get_config_file()
    if config_file.exists():
        response = typer.confirm("⚠️  La configuration existe déjà. Voulez-vous la réinitialiser?")
        if not response:
            print("❌ Opération annulée")
            return
    
    print("🎯 Initialisation de la configuration MeshDrive Host...\n")
    
    # Demander les paramètres
    host = typer.prompt("📍 Adresse IP du serveur", default="0.0.0.0")
    port = typer.prompt("🔌 Port du serveur", default=8000, type=int)
    
    keys_dir_input = typer.prompt("📁 Dossier des clés", default="keys")
    chunks_dir_input = typer.prompt("📦 Dossier des chunks", default="output")
    
    chunk_size = typer.prompt("📏 Taille des chunks (MB)", default=1, type=int)
    chunk_size_bytes = chunk_size * 1024 * 1024
    
    reload = typer.confirm("🔄 Mode rechargement automatique", default=True)
    
    # Convertir les chemins relatifs en chemins absolus basés sur le projet
    if not Path(keys_dir_input).is_absolute():
        keys_dir = str((PROJECT_ROOT / keys_dir_input).absolute())
    else:
        keys_dir = str(Path(keys_dir_input).absolute())
    
    if not Path(chunks_dir_input).is_absolute():
        chunks_dir = str((PROJECT_ROOT / chunks_dir_input).absolute())
    else:
        chunks_dir = str(Path(chunks_dir_input).absolute())
    
    config = {
        "host": host,
        "port": port,
        "keys_dir": keys_dir,
        "chunks_dir": chunks_dir,
        "chunk_size": chunk_size_bytes,
        "reload": reload,
        "log_level": "info"
    }
    
    save_config(config)
    
    # Créer les répertoires
    Path(config["keys_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["chunks_dir"]).mkdir(parents=True, exist_ok=True)
    
    print("\n✅ Configuration initialisée avec succès!")
    print("\n💡 Vous pouvez maintenant démarrer le serveur avec:")
    print("   meshdrive-host start")


if __name__ == "__main__":
    app()

