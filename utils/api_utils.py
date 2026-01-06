"""
Fonctions utilitaires communes pour les APIs de reconnaissance faciale.
"""
import os
import json
import numpy as np
from insightface.app import FaceAnalysis
from numpy.linalg import norm
from const import DB_FILE, SEUIL_RECONNAISSANCE

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
        app_face.prepare(ctx_id=0, det_size=(640, 640))     # Possible d'ajuster pour la performance
        modele_pret = True
        print("Modèle chargé")
    except Exception as e:
        modele_erreur = str(e)
        print(f"Erreur de chargement : {e}")


def get_model():
    """Retourne le modèle chargé."""
    return app_face


def is_model_ready():
    """Retourne True si le modèle est prêt."""
    return modele_pret


def get_model_error():
    """Retourne l'erreur du modèle s'il y en a une."""
    return modele_erreur


def save_vector_db(prenom, vecteur):
    """
    Sauvegarde le vecteur facial dans la base de données.
    """
    global base_cache
    
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
