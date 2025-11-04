"""
Script de test pour l'API FastAPI cryptolib
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_health():
    """Test du endpoint de santé"""
    print("🔍 Test: Health check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_list_files():
    """Test du listing des fichiers"""
    print("\n🔍 Test: List files")
    try:
        response = requests.get(f"{BASE_URL}/files")
        print(f"   Status: {response.status_code}")
        files = response.json()
        print(f"   Nombre de fichiers: {len(files)}")
        if files:
            print(f"   Premier fichier: {files[0]}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_encrypt_file(file_path: str):
    """Test du chiffrement d'un fichier"""
    print(f"\n🔍 Test: Encrypt file ({file_path})")
    try:
        if not Path(file_path).exists():
            print(f"   ⚠️  Fichier introuvable: {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            response = requests.post(f"{BASE_URL}/encrypt", files=files)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Fichier chiffré!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Nom: {result['original_name']}")
            print(f"   Chunks: {result['chunk_count']}")
            return result['file_id']
        else:
            print(f"   ❌ Erreur: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None


def test_get_file_info(file_id: str):
    """Test de récupération des infos d'un fichier"""
    print(f"\n🔍 Test: Get file info ({file_id})")
    try:
        response = requests.get(f"{BASE_URL}/files/{file_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            info = response.json()
            print(f"   ✅ Infos récupérées!")
            print(f"   Nom: {info['name']}")
            print(f"   Taille: {info['size']} bytes")
            print(f"   Algorithme: {info['algorithm']}")
            return True
        else:
            print(f"   ❌ Erreur: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_decrypt_file(file_id: str, output_path: str = None):
    """Test du déchiffrement d'un fichier"""
    print(f"\n🔍 Test: Decrypt file ({file_id})")
    try:
        response = requests.get(f"{BASE_URL}/decrypt/{file_id}?download=true")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Fichier déchiffré et sauvegardé: {output_path}")
            else:
                print(f"   ✅ Fichier déchiffré ({len(response.content)} bytes)")
            return True
        else:
            print(f"   ❌ Erreur: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🧪 Tests de l'API FastAPI MeshDrive Crypto")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ L'API n'est pas accessible. Vérifiez qu'elle est lancée.")
        return
    
    # Test 2: List files
    test_list_files()
    
    # Test 3: Encrypt (si un fichier de test est disponible)
    test_file = Path(__file__).parent.parent / "README.md"
    if test_file.exists():
        file_id = test_encrypt_file(str(test_file))
        
        if file_id:
            # Test 4: Get file info
            test_get_file_info(file_id)
            
            # Test 5: Decrypt (optionnel - décommenter pour tester)
            # test_decrypt_file(file_id, "test_decrypted.md")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)


if __name__ == "__main__":
    main()

