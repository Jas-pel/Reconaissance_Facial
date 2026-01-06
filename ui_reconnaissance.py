import streamlit as st
import requests
import time
from const import API_URL_RECO, API_URL_STATUS


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
    """Affiche le résultat de la reconnaissance et retourne le nom."""
    if not r:
        return None
    
    if r["status"] == "no_face":
        st.error("❌ Aucun visage détecté")
        return None
    elif r["status"] == "no_db":
        st.warning("⚠️ Base de données vide")
        return None
    else:
        identite = r.get('identite', 'Inconnu')
        score = r.get('score', 0)
        
        st.subheader("🔍 Résultat de la reconnaissance")
        st.metric("Score de confiance", f"{score:.3f}")
        
        if score >= 0.35 and identite != "Inconnu":
            st.success(f"✅ Bonjour **{identite}** !")
            return identite
        else:
            st.error("❌ Personne non reconnue")
            return "Inconnu"


# Configuration de la page
st.set_page_config(page_title="Reconnaissance Faciale", page_icon="🔍")
st.title("🔍 Reconnaissance Faciale")

# Capture photo
photo = st.camera_input("Prendre une photo")

if photo:
    if not attendre_api_et_modele():
        st.stop()

    with st.spinner("Analyse en cours..."):
        files = {"file": photo.getvalue()}
        
        r = appeler_api(API_URL_RECO, files)
        if r and r["status"] == "model_not_ready":
            if attendre_api_et_modele():
                r = appeler_api(API_URL_RECO, files)
        
        # Afficher le résultat et récupérer le nom
        nom_personne = afficher_resultat_reconnaissance(r)
        
        # Stocker le résultat dans le session state pour un accès ultérieur
        if nom_personne and nom_personne != "Inconnu":
            st.session_state['derniere_personne_reconnue'] = nom_personne
            
            # Message pour usage programmatique
            st.info(f"💾 Résultat stocké : {nom_personne}")
