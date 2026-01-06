import streamlit as st
import sys
import os

# Ajouter la racine du projet au path pour Streamlit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from const import API_URL_RECO, API_URL_STATUS_RECONNAISSANCE
from utils.ui_utils import attendre_api_et_modele, appeler_api


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
st.title("Reconnaissance")

# Capture photo
photo = st.camera_input("Prendre une photo")

if photo:
    if not attendre_api_et_modele(API_URL_STATUS_RECONNAISSANCE):
        st.stop()

    with st.spinner("Analyse en cours..."):
        files = {"file": photo.getvalue()}
        
        r = appeler_api(API_URL_RECO, files, api_url_status=API_URL_STATUS_RECONNAISSANCE)
        if r and r["status"] == "model_not_ready":
            if attendre_api_et_modele(API_URL_STATUS_RECONNAISSANCE):
                r = appeler_api(API_URL_RECO, files, api_url_status=API_URL_STATUS_RECONNAISSANCE)
        
        # Afficher le résultat et récupérer le nom
        nom_personne = afficher_resultat_reconnaissance(r)
        
        # Stocker le résultat dans le session state pour un accès ultérieur
        if nom_personne and nom_personne != "Inconnu":
            st.session_state['derniere_personne_reconnue'] = nom_personne
            
            # Message pour usage programmatique
            st.info(f"💾 Résultat stocké : {nom_personne}")
