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

# Définition des 3 étapes de capture
ETAPES_CAPTURE = [
    {"id": "face", "label": "Photo 1/3 : Visage de FACE", "instruction": "Regardez directement la caméra, visage bien centré."},
    {"id": "gauche", "label": "Photo 2/3 : Visage tourné vers la GAUCHE", "instruction": "Tournez légèrement votre tête vers la gauche (environ 30°)."},
    {"id": "droite", "label": "Photo 3/3 : Visage tourné vers la DROITE", "instruction": "Tournez légèrement votre tête vers la droite (environ 30°)."},
]

# Initialisation du state pour l'enrôlement multi-photos
if 'etape_capture' not in st.session_state:
    st.session_state.etape_capture = 0  # 0, 1, 2 pour les 3 étapes
if 'photos_validees' not in st.session_state:
    st.session_state.photos_validees = []  # Liste des photos validées
if 'enrollment_prenom' not in st.session_state:
    st.session_state.enrollment_prenom = ""


def reinitialiser_enrolement():
    """Réinitialise le processus d'enrôlement."""
    st.session_state.etape_capture = 0
    st.session_state.photos_validees = []
    st.session_state.enrollment_prenom = ""
    if 'force_enroll' in st.session_state:
        del st.session_state['force_enroll']


def traiter_photo(photo_bytes, prenom, force_enroll, is_first_photo):
    """
    Traite une photo et l'envoie à l'API.
    
    Args:
        photo_bytes: Bytes de la photo
        prenom: Prénom de l'utilisateur
        force_enroll: Force le ré-enrôlement
        is_first_photo: True si c'est la première photo (vérifie si déjà enregistré)
    
    Returns:
        dict: {"success": bool, "message": str, "already_registered": bool, "identite": str, "score": float}
    """
    files = {"file": photo_bytes}
    # Pour les photos suivantes, on force l'enrôlement car on a déjà validé
    effective_force = force_enroll if is_first_photo else True
    
    r = appeler_api(
        API_URL_ENROLL, 
        files, 
        params={"prenom": prenom, "force_enroll": effective_force}, 
        api_url_status=API_URL_STATUS_APPRENTISSAGE
    )
    
    if not r:
        return {"success": False, "message": "Erreur de communication avec l'API", "already_registered": False}
    
    if r["status"] == "ok":
        return {"success": True, "message": "Photo validée !", "already_registered": False}
    elif r["status"] == "already_registered":
        return {
            "success": False, 
            "message": f"Visage déjà enregistré sous le nom {r['identite']}", 
            "already_registered": True,
            "identite": r["identite"],
            "score": r["score"]
        }
    elif r["status"] == "no_face":
        return {"success": False, "message": "Aucun visage détecté", "already_registered": False}
    elif r["status"] == "model_not_ready":
        return {"success": False, "message": "Modèle non prêt", "already_registered": False}
    else:
        return {"success": False, "message": "Erreur inconnue", "already_registered": False}


# ===== INTERFACE PRINCIPALE =====

# Afficher la progression
etape_actuelle = st.session_state.etape_capture
photos_validees = len(st.session_state.photos_validees)

if etape_actuelle < 3:
    st.progress(photos_validees / 3, text=f"Progression : {photos_validees}/3 photos capturées")
else:
    st.progress(1.0, text="✅ Enrôlement terminé !")

# Bouton de réinitialisation (toujours visible si on a commencé)
if photos_validees > 0 or st.session_state.enrollment_prenom:
    if st.button("🔄 Recommencer l'enrôlement"):
        reinitialiser_enrolement()
        st.rerun()

# Entrée du prénom (seulement à l'étape 0 et si pas encore validé)
if etape_actuelle == 0 and not st.session_state.enrollment_prenom:
    prenom = st.text_input("Entrez votre prénom")
    if prenom:
        st.session_state.enrollment_prenom = prenom
        st.rerun()
elif st.session_state.enrollment_prenom:
    st.info(f"Enrôlement en cours pour : **{st.session_state.enrollment_prenom}**")

# Processus de capture des 3 photos
if st.session_state.enrollment_prenom and etape_actuelle < 3:
    etape = ETAPES_CAPTURE[etape_actuelle]
    
    st.subheader(etape["label"])
    st.write(f"💡 **Instruction** : {etape['instruction']}")
    
    # Capture photo
    photo = st.camera_input(f"Capturer - {etape['id']}", key=f"camera_{etape['id']}_{etape_actuelle}")
    
    if photo:
        if not attendre_api_et_modele(API_URL_STATUS_APPRENTISSAGE):
            st.stop()
        
        with st.spinner("Analyse en cours..."):
            prenom = st.session_state.enrollment_prenom
            force_enroll = st.session_state.get('force_enroll', False)
            is_first_photo = (etape_actuelle == 0 and photos_validees == 0)
            
            result = traiter_photo(photo.getvalue(), prenom, force_enroll, is_first_photo)
            
            if result["success"]:
                st.success(f"✅ {result['message']} ({etape['id']})")
                st.session_state.photos_validees.append(etape["id"])
                st.session_state.etape_capture += 1
                
                # Vérifier si c'était la dernière photo
                if st.session_state.etape_capture >= 3:
                    st.balloons()
                    st.success("**Enrôlement complet !** Les 3 photos ont été enregistrées avec succès.")
                else:
                    st.info("➡️ Passez à la photo suivante...")
                    st.rerun()
                    
            elif result.get("already_registered"):
                st.warning(f"⚠️ Vous avez déjà été enregistré sous le nom **{result['identite']}** (score: {result['score']:.3f}). Voulez-vous vous ré-enrôler pour améliorer la reconnaissance ?")
                if st.button("🔄 Oui, ré-enrôler maintenant"):
                    st.session_state['force_enroll'] = True
                    st.rerun()
            else:
                st.error(f"❌ {result['message']}")
                st.write("Veuillez reprendre la photo.")

# Affichage du résumé final
elif etape_actuelle >= 3:
    st.success("**Enrôlement terminé avec succès !**")
    st.write(f"**Utilisateur** : {st.session_state.enrollment_prenom}")
    st.write(f"**Photos enregistrées** : {', '.join(st.session_state.photos_validees)}")
    st.write("Vous pouvez maintenant utiliser la reconnaissance faciale.")
    
    if st.button("Enrôler une autre personne"):
        reinitialiser_enrolement()
        st.rerun()
