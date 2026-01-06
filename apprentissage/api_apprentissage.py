import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
import uvicorn
import threading

from utils.api_utils import (
    charger_modele, get_model, is_model_ready, get_model_error,
    save_vector_db, load_bd, redimensionner_image, reconnaitre
)

api = FastAPI()


def start_api():
    """
    Initialise et démarre l'API FastAPI pour l'apprentissage.
    """
    # Démarrer le chargement du modèle en arrière-plan
    thread = threading.Thread(target=charger_modele, daemon=True)
    thread.start()
    
    uvicorn.run(api, host="127.0.0.1", port=8000, log_level="error")


# --------- Endpoints ---------
@api.get("/status")
async def get_status():
    """Retourne l'état du modèle."""
    modele_erreur = get_model_error()
    if modele_erreur:
        return {"status": "error", "message": modele_erreur}
    elif is_model_ready():
        return {"status": "ready"}
    else:
        return {"status": "loading"}


@api.post("/enroll")
async def enroll(prenom: str, file: UploadFile = File(...), force_enroll: bool = False):
    """
    Permet d'enrôler un nouveau visage.
    Si force_enroll=True, ré-enrôle même si le visage existe déjà.
    """
    if not is_model_ready():
        return {"status": "model_not_ready"}
    
    image_bytes = await file.read()
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
    img = redimensionner_image(img, max_size=640)  # Optimisation
    
    app_face = get_model()
    faces = app_face.get(img)   # type: ignore
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
