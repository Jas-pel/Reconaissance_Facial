import streamlit as st
import requests
import time
from const import API_URL_ENROLL, API_URL_RECO, API_URL_STATUS


def attendre_api_et_modele():
    """Attend que l'API et le modèle soient prêts."""
    with st.spinner("Démarrage de l'API..."):
        debut = time.time()
        while time.time() - debut < 30:
            try:
                requests.get(API_URL_STATUS, timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        else:
            st.error("Impossible de se connecter à l'API.")
            return False

    with st.spinner("Chargement du modèle..."):
        debut = time.time()
        while time.time() - debut < 60:
            try:
                status = requests.get(API_URL_STATUS, timeout=1).json().get("status")
                if status == "ready":
                    return True
                if status == "error":
                    st.error("Erreur lors du chargement du modèle.")
                    return False
            except Exception:
                pass
            time.sleep(0.5)
        st.error("Timeout : le modèle prend trop de temps à charger.")
        return False


def appeler_api(url, files, params=None):
    """Appelle l'API avec gestion automatique des erreurs et attentes."""
    try:
        response = requests.post(url, params=params, files=files, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.warning("Délai dépassé, nouvelle tentative après vérification du modèle...")
        if attendre_api_et_modele():
            try:
                response = requests.post(url, params=params, files=files, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur API après nouvel essai : {e}")
        return None
    except requests.exceptions.ConnectionError:
        if attendre_api_et_modele():
            try:
                response = requests.post(url, params=params, files=files, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur API après reconnexion : {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur API : {e}")
        return None


def afficher_resultat_reconnaissance(r):
    """Affiche le résultat de la reconnaissance."""
    if not r:
        return
    
    if r["status"] == "no_face":
        st.error("Aucun visage détecté")
    elif r["status"] == "no_db":
        st.warning("Base vide")
    else:
        st.subheader("Résultat")
        st.metric("Score de confiance", f"{r['score']:.3f}")
        if r['score'] >= 0.35:
            st.success(f"Bonjour **{r['identite']}** !")
        else:
            st.error("Personne non reconnue")  


st.set_page_config(page_title="Reconnaissance Faciale", page_icon="👤")
st.title("Reconnaissance / Enrôlement Biométrique")

# État du modèle
model_status = "unknown"
try:
    status_response = requests.get(API_URL_STATUS, timeout=0.5)
    model_status = status_response.json().get("status")
except:
    model_status = "unknown"


mode = st.radio("Mode :", ["Enrôlement", "Reconnaissance"])

prenom = ""
if mode == "Enrôlement":
    prenom = st.text_input("Entrez votre prénom")

photo = st.camera_input("Prendre une photo")

if photo:
    if not attendre_api_et_modele():
        st.stop()

    with st.spinner("Analyse en cours..."):
        files = {"file": photo.getvalue()}

        if mode == "Enrôlement":
            if not prenom:
                st.warning("Veuillez entrer votre prénom.")
            else:
                r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom})
                if r:
                    if r["status"] == "ok":
                        st.success("Enrôlement réussi !")
                        st.balloons()
                    elif r["status"] == "model_not_ready":
                        if attendre_api_et_modele():
                            r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom})
                            if r and r["status"] == "ok":
                                st.success("Enrôlement réussi !")
                                st.balloons()
                            else:
                                st.error("Visage non détecté")
                    else:
                        st.error("Visage non détecté")

        else:  # Reconnaissance
            r = appeler_api(API_URL_RECO, files)
            if r and r["status"] == "model_not_ready":
                if attendre_api_et_modele():
                    r = appeler_api(API_URL_RECO, files)
            afficher_resultat_reconnaissance(r)
