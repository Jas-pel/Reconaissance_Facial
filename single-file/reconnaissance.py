"""
Reconnaissance (single-file)
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
SEUIL_RECONNAISSANCE = 0.35  # 0..1 (plus haut = plus strict)


# --------- Utilitaires base de données ---------
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


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


# --------- Affichage du résultat ---------
def afficher_resultat_reconnaissance(identite, score):
    """Affiche le résultat de la reconnaissance."""
    st.subheader("🔍 Résultat de la reconnaissance")
    st.metric("Score de confiance", f"{score:.3f}")
    
    if score >= SEUIL_RECONNAISSANCE and identite != "Inconnu":
        st.success(f"✅ Bonjour **{identite}** !")
        return identite
    else:
        st.error("❌ Personne non reconnue")
        return "Inconnu"


# --------- UI Streamlit ---------
st.set_page_config(page_title="Reconnaissance Faciale", page_icon="🔍")
st.title("Reconnaissance")

with st.spinner("Chargement du modèle InsightFace (CPU)..."):
    app_face = get_model()

# Capture photo
photo = st.camera_input("Prendre une photo")

if photo:
    base = load_db()
    if not base:
        st.warning("⚠️ La base de données est vide. Enrôlez d'abord quelqu'un avec l'application d'apprentissage.")
    else:
        with st.spinner("Analyse en cours..."):
            image_bytes = photo.getvalue()
            img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
            
            faces = app_face.get(img)  # type: ignore
            if not faces:
                st.error("❌ Aucun visage détecté")
            else:
                vecteur = faces[0].embedding
                identite, score = reconnaitre(vecteur, base)
                afficher_resultat_reconnaissance(identite, score)
