import threading
import API.run_api as run_api
import host.cli  as cli

if __name__ == "__main__":
    # Thread pour FastAPI
    api_thread = threading.Thread(target=run_api.main, daemon=True)
    api_thread.start()

    # Lancer ton CLI dans le thread principal
    ## cli.app()
