"""
Apprentissage (single-file) - Enrôlement avec 3 photos
Tout est auto-suffisant dans ce fichier, pas besoin d'API externe.
"""
import os
import json
import cv2
import numpy as np
import streamlit as st
from insightface.app import FaceAnalysis

# --------- Configuration locale (auto-suffisante) ---------
SCRIPT_DIR = os.path.dirname(__file__)
DB_FILE = os.path.join(SCRIPT_DIR, "base_donnees_visages.json")
SEUIL_RECONNAISSANCE = 0.35 


# --------- Utilitaires base de données ---------
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_vector_db(prenom, vecteur):
    data = load_db()
    data.append({
        "identifiant": prenom,
        "vecteur": vecteur.tolist(),
    })
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------- Similarité & reconnaissance ---------
def cosine_similarity(v1, v2):
    v1 = np.asarray(v1, dtype=np.float32)
    v2 = np.asarray(v2, dtype=np.float32)
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)


def reconnaitre(vecteur, base):
    meilleur_score = -1.0
    meilleure_identite = None
    for entree in base:
        v_db = np.array(entree["vecteur"], dtype=np.float32)
        score = cosine_similarity(vecteur, v_db)
        if score > meilleur_score:
            meilleur_score = score
            meilleure_identite = entree["identifiant"]
    if meilleur_score < SEUIL_RECONNAISSANCE:
        meilleure_identite = "Inconnu"
    return meilleure_identite, meilleur_score


# --------- Chargement du modèle (CPU par défaut) ---------
@st.cache_resource(show_spinner=False)
def get_model():
    app = FaceAnalysis(name="buffalo_l")
    # ctx_id=-1 => CPU (plus compatible, plus lent)
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app


# --------- Traitement d'une photo ---------
def traiter_photo(app_face, photo_bytes, prenom, force_enroll, is_first_photo):
    """
    Traite une photo et l'enregistre si valide.
    
    Returns:
        dict: {"success": bool, "message": str, "already_registered": bool, "identite": str, "score": float}
    """
    img = cv2.imdecode(np.frombuffer(photo_bytes, np.uint8), 1)
    
    faces = app_face.get(img)  # type: ignore
    if not faces:
        return {"success": False, "message": "Aucun visage détecté", "already_registered": False}
    
    vecteur = faces[0].embedding
    base = load_db()
    
    # Vérifier si déjà enregistré (seulement pour la première photo et si pas force_enroll)
    if is_first_photo and not force_enroll and base:
        identite, score = reconnaitre(vecteur, base)
        if identite != "Inconnu":
            return {
                "success": False,
                "message": f"Visage déjà enregistré sous le nom {identite}",
                "already_registered": True,
                "identite": identite,
                "score": score
            }
    
    # Enregistrer le vecteur
    save_vector_db(prenom, vecteur)
    return {"success": True, "message": "Photo validée !", "already_registered": False}


# --------- UI Streamlit ---------
st.set_page_config(page_title="Apprentissage - Enrôlement", page_icon="📝")
st.title("Apprentissage - Enrôlement Biométrique")

with st.spinner("Chargement du modèle InsightFace (CPU)..."):
    app_face = get_model()

# Définition des 3 étapes de capture
ETAPES_CAPTURE = [
    {"id": "face", "label": "Photo 1/3 : Visage de FACE", "instruction": "Regardez directement la caméra, visage bien centré."},
    {"id": "gauche", "label": "Photo 2/3 : Visage tourné vers la GAUCHE", "instruction": "Tournez légèrement votre tête vers la gauche (environ 30°)."},
    {"id": "droite", "label": "Photo 3/3 : Visage tourné vers la DROITE", "instruction": "Tournez légèrement votre tête vers la droite (environ 30°)."},
]

# Initialisation du state pour l'enrôlement multi-photos
if "etape_capture" not in st.session_state:
    st.session_state.etape_capture = 0  # 0, 1, 2 pour les 3 étapes
if "photos_validees" not in st.session_state:
    st.session_state.photos_validees = []  # Liste des photos validées
if "enrollment_prenom" not in st.session_state:
    st.session_state.enrollment_prenom = ""


def reinitialiser_enrolement():
    """Réinitialise le processus d'enrôlement."""
    st.session_state.etape_capture = 0
    st.session_state.photos_validees = []
    st.session_state.enrollment_prenom = ""
    if "force_enroll" in st.session_state:
        del st.session_state["force_enroll"]


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
        with st.spinner("Analyse en cours..."):
            prenom = st.session_state.enrollment_prenom
            force_enroll = st.session_state.get("force_enroll", False)
            is_first_photo = (etape_actuelle == 0 and photos_validees == 0)
            
            result = traiter_photo(app_face, photo.getvalue(), prenom, force_enroll, is_first_photo)
            
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
                    st.session_state["force_enroll"] = True
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