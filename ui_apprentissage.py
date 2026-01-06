import streamlit as st
import requests
import time
from const import API_URL_ENROLL, API_URL_STATUS


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


# Configuration de la page
st.set_page_config(page_title="Apprentissage - Enrôlement", page_icon="📝")
st.title("Apprentissage - Enrôlement Biométrique")

# Entrée du prénom
prenom = st.text_input("Entrez votre prénom")

# Capture photo
photo = st.camera_input("Prendre une photo")

if photo:
    if not attendre_api_et_modele():
        st.stop()

    with st.spinner("Analyse en cours..."):
        files = {"file": photo.getvalue()}

        if not prenom:
            st.warning("Veuillez entrer votre prénom.")
        else:
            # Vérifier si on est en mode de confirmation de ré-enrôlement
            force_enroll = st.session_state.get('force_enroll', False)
            
            r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom, "force_enroll": force_enroll})
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
                    if attendre_api_et_modele():
                        r = appeler_api(API_URL_ENROLL, files, params={"prenom": prenom, "force_enroll": force_enroll})
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
