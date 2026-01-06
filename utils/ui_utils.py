"""
Fonctions utilitaires communes pour les interfaces Streamlit.
"""
import streamlit as st
import requests
import time


def attendre_api_et_modele(api_url_status):
    """
    Attend que l'API et le modèle soient prêts.
    
    Args:
        api_url_status: URL de l'endpoint status de l'API
        
    Returns:
        bool: True si l'API est prête, False sinon
    """
    with st.spinner("Démarrage de l'API..."):
        debut = time.time()
        while time.time() - debut < 30:
            try:
                requests.get(api_url_status, timeout=1)
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
                status = requests.get(api_url_status, timeout=1).json().get("status")
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


def appeler_api(url, files, params=None, api_url_status=None):
    """
    Appelle l'API avec gestion automatique des erreurs et attentes.
    
    Args:
        url: URL de l'endpoint à appeler
        files: Fichiers à envoyer
        params: Paramètres optionnels
        api_url_status: URL de l'endpoint status pour la reconnexion (optionnel)
        
    Returns:
        dict: Réponse JSON de l'API ou None en cas d'erreur
    """
    try:
        response = requests.post(url, params=params, files=files, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.warning("Délai dépassé, nouvelle tentative après vérification du modèle...")
        if api_url_status and attendre_api_et_modele(api_url_status):
            try:
                response = requests.post(url, params=params, files=files, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur API après nouvel essai : {e}")
        return None
    except requests.exceptions.ConnectionError:
        if api_url_status and attendre_api_et_modele(api_url_status):
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
