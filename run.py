import subprocess
import sys

if __name__ == "__main__":

    # Lancer l'API en arrière-plan avec le modèle qui se charge en parallèle
    print("Démarrage de l'API (le modèle se chargera en arrière-plan)...")
    api_process = subprocess.Popen([sys.executable, "-c", "from api_face import start_api; start_api()"])
    
    # Lancer l'UI Streamlit (qui s'affichera immédiatement)
    print("Démarrage de l'interface Streamlit...")
    subprocess.run(["streamlit", "run", "ui_streamlit.py"])