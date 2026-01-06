import streamlit as st
import sys
import os

# Ajouter la racine du projet au path pour Streamlit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from const import API_URL_ENROLL, API_URL_STATUS_APPRENTISSAGE
from utils.ui_utils import attendre_api_et_modele, appeler_api


# Configuration de la page
st.set_page_config(page_title="Apprentissage - Enrôlement", page_icon="📝")
st.title("Apprentissage - Enrôlement Biométrique")

# Entrée du prénom
prenom = st.text_input("Entrez votre prénom")

# Capture photo
photo = st.camera_input("Prendre une photo")

if photo:
    if not attendre_api_et_modele(API_URL_STATUS_APPRENTISSAGE):
        st.stop()

    with st.spinner("Analyse en cours..."):
        files = {"file": photo.getvalue()}

        if not prenom:
            st.warning("Veuillez entrer votre prénom.")
        else:
            # Vérifier si on est en mode de confirmation de ré-enrôlement
            force_enroll = st.session_state.get('force_enroll', False)
            
            r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom, "force_enroll": force_enroll}, api_url_status=API_URL_STATUS_APPRENTISSAGE)
            if r:
                if r["status"] == "ok":
                    st.success("✅ Enrôlement réussi !")
                    st.balloons()
                    # Réinitialiser le flag
                    if 'force_enroll' in st.session_state:
                        del st.session_state['force_enroll']
                elif r["status"] == "already_registered":
                    st.warning(f"⚠️ Vous avez déjà été enregistré sous le nom **{r['identite']}** (score: {r['score']:.3f})\n\n💡 Voulez-vous vous ré-enrôler pour de meilleurs résultats ?")
                    if st.button("🔄 Oui, ré-enrôler maintenant"):
                        st.session_state['force_enroll'] = True
                        st.rerun()
                elif r["status"] == "model_not_ready":
                    if attendre_api_et_modele(API_URL_STATUS_APPRENTISSAGE):
                        r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom, "force_enroll": force_enroll}, api_url_status=API_URL_STATUS_APPRENTISSAGE)
                        if r and r["status"] == "ok":
                            st.success("✅ Enrôlement réussi !")
                            st.balloons()
                            if 'force_enroll' in st.session_state:
                                del st.session_state['force_enroll']
                        elif r and r["status"] == "already_registered":
                            st.warning(f"⚠️ Vous avez déjà été enregistré sous le nom **{r['identite']}** (score: {r['score']:.3f})\n\n💡 Voulez-vous vous ré-enrôler pour de meilleurs résultats ?")
                            if st.button("🔄 Oui, ré-enrôler maintenant"):
                                st.session_state['force_enroll'] = True
                                st.rerun()
                        else:
                            st.error("❌ Visage non détecté")
                else:
                    st.error("❌ Visage non détecté")
