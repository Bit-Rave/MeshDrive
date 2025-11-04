from py2p import mesh
import socket
import os
import time

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

RECEIVE_DIR = "fichiers_recus"
os.makedirs(RECEIVE_DIR, exist_ok=True)

listener = mesh.MeshSocket('0.0.0.0', 5000)
print(f"\n🖥️ En écoute sur {get_local_ip()}:5000")
print(f"📁 Dossier de réception : {RECEIVE_DIR}\n")

try:
    while True:
        msg = listener.recv(1)
        if not msg or isinstance(msg, int):
            time.sleep(0.1)
            continue

        # On prend packets de msg
        try:
            packets = msg.packets
            # On suppose que le premier élément utile est packets[1] (car [type, data])
            data = packets[1] if len(packets) > 1 else None
        except Exception as e:
            print(f"⚠️ Erreur en lisant le message : {e}")
            continue

        if not data:
            print("⚠️ Message reçu mais vide ou inconnu.")
            continue

        if isinstance(data, bytes) and data.startswith(b"FILE:"):
            try:
                header, file_data = data.split(b"|", 1)
                filename = header.decode(errors="ignore").split("FILE:",1)[1]
                save_path = os.path.join(RECEIVE_DIR, filename)
                with open(save_path, "wb") as f:
                    f.write(file_data)
                print(f"✅ Fichier reçu : {filename} ({len(file_data)} octets)")
            except Exception as e:
                print(f"❌ Erreur lors du traitement du fichier : {e}")
        else:
            try:
                print(f"🔹 Message texte reçu : {data.decode(errors='ignore')[:100]}")
            except:
                print(f"🔹 Message binaire reçu ({len(data)} octets)")

except KeyboardInterrupt:
    print("\n✋ Arrêt du récepteur.")
