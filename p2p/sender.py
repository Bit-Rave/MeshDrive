from py2p import mesh
import time
import os

RECEIVER_IP = "192.168.1.58"  # ← à adapter
RECEIVER_PORT = 5000

sender = mesh.MeshSocket('0.0.0.0', 5001)
print(f"🔗 Connexion à {RECEIVER_IP}:{RECEIVER_PORT}...")
sender.connect(RECEIVER_IP, RECEIVER_PORT)
time.sleep(2)
print("✅ Connecté !\n")

try:
    while True:
        chemin = input("📁 Chemin du fichier à envoyer (ou 'q' pour quitter) : ").strip()
        if chemin.lower() == 'q':
            break
        if not os.path.isfile(chemin):
            print("❌ Fichier introuvable.\n")
            continue

        filename = os.path.basename(chemin)
        with open(chemin, 'rb') as f:
            file_data = f.read()

        full_message = f"FILE:{filename}|".encode() + file_data

        # Envoi via send()
        sender.send(full_message)

        print(f"✅ Fichier envoyé : {filename} ({len(file_data)} octets)\n")

except KeyboardInterrupt:
    print("\n✋ Arrêt de l’émetteur.")
