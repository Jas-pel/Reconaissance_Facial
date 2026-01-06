import subprocess
import sys

if __name__ == "__main__":

    # Lancer l'API d'apprentissage en arrière-plan avec le modèle qui se charge en parallèle
    print("Démarrage de l'API d'apprentissage (le modèle se chargera en arrière-plan)...")
    api_process = subprocess.Popen([sys.executable, "-c", "from apprentissage.api_apprentissage import start_api; start_api()"])
    
    # Lancer l'UI Streamlit pour l'apprentissage
    print("Démarrage de l'interface d'apprentissage...")
    subprocess.run(["streamlit", "run", "apprentissage/ui_apprentissage.py"])
