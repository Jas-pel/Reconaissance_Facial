import os
import json
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
import uvicorn
from insightface.app import FaceAnalysis
from numpy.linalg import norm
from const import DB_FILE, SEUIL_RECONNAISSANCE
import threading

api = FastAPI()

# Variables globales pour le modèle
app_face = None
modele_pret = False
modele_erreur = None

# Cache pour la base de données
base_cache = None
base_cache_time = 0


def charger_modele():
    """
    Charge le modèle InsightFace en arrière-plan.
    """
    global app_face, modele_pret, modele_erreur
    try:
        print("Chargement du modèle InsightFace...")
        app_face = FaceAnalysis(name="buffalo_l")
        app_face.prepare(ctx_id=0, det_size=(320, 320))  # Réduit de 640 à 320 pour +rapidité
        modele_pret = True
        print("Modèle chargé")
    except Exception as e:
        modele_erreur = str(e)
        print(f"Erreur de chargement : {e}")


def save_vector_db(prenom, vecteur):
    """
    Sauvegarde le vecteur facial dans la base de données.
    """
    global base_cache, base_cache_time
    
    data = []

    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            
    data.append({
        "identifiant": prenom,
        "vecteur": vecteur.tolist()
    })

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
    
    # Invalider le cache
    base_cache = None


def load_bd():
    """
    Charge la base de données des visages avec mise en cache.
    """
    global base_cache, base_cache_time
    
    if not os.path.exists(DB_FILE):
        return []
    
    # Vérifier si le fichier a été modifié
    mtime = os.path.getmtime(DB_FILE)
    if base_cache is not None and mtime == base_cache_time:
        return base_cache
    
    with open(DB_FILE, "r") as f:
        base_cache = json.load(f)
        base_cache_time = mtime
        return base_cache


def redimensionner_image(img, max_size=640):
    """
    Redimensionne l'image si elle est trop grande pour accélérer le traitement.
    """
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img


def similarite_cosinus(v1, v2):
    """
    Retourne la similarité cosinus entre deux vecteurs.
    """
    return np.dot(v1, v2) / (norm(v1) * norm(v2))


def reconnaitre(vecteur, base):
    """
    Regarde dans la base pour trouver le visage le plus similaire.
    Retourne l'identité et le score de similarité.
    """
    meilleur_score = -1
    meilleure_identite = None
    for entree in base:
        v_db = np.array(entree["vecteur"])
        score = similarite_cosinus(vecteur, v_db)
        if score > meilleur_score:
            meilleur_score = score
            meilleure_identite = entree["identifiant"]

    if meilleur_score < SEUIL_RECONNAISSANCE:
        meilleure_identite = "Inconnu"
    return meilleure_identite, meilleur_score


def start_api():
    """
    Initialise et démarre l'API FastAPI.
    """
    # Démarrer le chargement du modèle en arrière-plan
    thread = threading.Thread(target=charger_modele, daemon=True)
    thread.start()
    
    uvicorn.run(api, host="127.0.0.1", port=8000, log_level="error")


# --------- Endpoints ---------
@api.get("/status")
async def get_status():
    """Retourne l'état du modèle."""
    if modele_erreur:
        return {"status": "error", "message": modele_erreur}
    elif modele_pret:
        return {"status": "ready"}
    else:
        return {"status": "loading"}


@api.post("/enroll")
async def enroll(prenom: str, file: UploadFile = File(...), force_enroll: bool = False):
    """
    Permet d'enrôler un nouveau visage.
    Si force_enroll=True, ré-enrôle même si le visage existe déjà.
    """
    if not modele_pret:
        return {"status": "model_not_ready"}
    
    image_bytes = await file.read()
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
    img = redimensionner_image(img, max_size=640)  # Optimisation
    faces = app_face.get(img)
    if not faces:
        return {"status": "no_face"}
    
    # Vérifier si le visage est déjà enregistré (sauf si force_enroll)
    vecteur = faces[0].embedding
    base = load_bd()
    if base and not force_enroll:
        identite, score = reconnaitre(vecteur, base)
        if identite != "Inconnu":
            return {"status": "already_registered", "identite": identite, "score": float(score)}
    
    save_vector_db(prenom, faces[0].embedding)
    return {"status": "ok"}


@api.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    """
    Permet de reconnaître un visage.
    """
    if not modele_pret:
        return {"status": "model_not_ready"}
    
    image_bytes = await file.read()
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
    img = redimensionner_image(img, max_size=640)  # Optimisation
    faces = app_face.get(img)
    if not faces:
        return {"status": "no_face"}
    vecteur = faces[0].embedding
    base = load_bd()
    if not base:
        return {"status": "no_db"}
    identite, score = reconnaitre(vecteur, base)
    return {"status": "ok", "identite": identite, "score": float(score)}

