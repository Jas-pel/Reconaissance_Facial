# Système de Reconnaissance Faciale

Projet de reconnaissance faciale utilisant InsightFace avec une architecture client-serveur moderne.

## Architecture

```
projet_opti/
├── run.py                          # Point d'entrée
├── api_face.py                     # Backend (API FastAPI)
├── ui_streamlit.py                 # Frontend (Interface)
├── const.py                        # Configuration
├── base_donnees_visages.json       # Base de données
└── __pycache__/
```

### Architecture Client-Serveur

- **Backend** : API REST avec FastAPI (port 8000)
- **Frontend** : Interface Streamlit (port 8501)
- **Modèle IA** : InsightFace (buffalo_l)
- **Communication** : HTTP REST

---

## 📁 Description des fichiers

### 1️⃣ `run.py` - Point d'entrée

**Rôle** : Lance les deux serveurs

```python
python run.py  # Lance tout le système
```

- Démarre l'API en arrière-plan
- Démarre l'interface Streamlit
- Gère l'ordre de démarrage optimal

---

### 2️⃣ `api_face.py` - Backend API

**Rôle** : API REST avec FastAPI

- **Port** : 8000
- **Modèle IA** : InsightFace (reconnaissance faciale)
- **Chargement** : Asynchrone en thread séparé

**Endpoints disponibles** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/status` | GET | Statut du modèle (loading/ready/error) |
| `/enroll` | POST | Enrôler un nouveau visage |
| `/recognize` | POST | Identifier un visage |

**Fonctionnalités** :
- Chargement asynchrone du modèle
- Détection de visage
- Calcul de vecteurs faciaux (embeddings)
- Similarité cosinus pour la reconnaissance

---

### 3️⃣ `ui_streamlit.py` - Frontend

**Rôle** : Interface web interactive

- **Port** : 8501
- **Framework** : Streamlit
- **Communication** : HTTP requests vers l'API

**Pages disponibles** :
-  **Page d'accueil** : Choix entre enrôlement et identification
-  **Page enrôlement** : Ajouter une nouvelle personne à la base
-  **Page identification** : Reconnaître une personne

**Fonctionnalités** :
- Capture photo via webcam
- Affichage du statut du modèle en temps réel
- Gestion des erreurs de connexion
- Attente automatique du chargement du modèle

---

### 4️⃣ `const.py` - Configuration

**Rôle** : Constantes partagées

```python
DB_FILE = "base_donnees_visages.json"
SEUIL_RECONNAISSANCE = 0.35
API_URL_ENROLL = "http://127.0.0.1:8000/enroll"
API_URL_RECO = "http://127.0.0.1:8000/recognize"
API_URL_STATUS = "http://127.0.0.1:8000/status"
```

---

### 5️⃣ `base_donnees_visages.json` - Base de données

**Rôle** : Stockage des vecteurs faciaux

```json
[
  {
    "identifiant": "Jean",
    "vecteur": [0.123, -0.456, 0.789, ...]
  },
  {
    "identifiant": "Marie",
    "vecteur": [0.321, -0.654, 0.987, ...]
  }
]
```

---

## 🔄 Flux de fonctionnement

```
1. run.py démarre
   ↓
2. API (port 8000) démarre → Modèle charge en thread
   ↓
3. Streamlit (port 8501) démarre → Interface visible immédiatement
   ↓
4. User prend une photo → Streamlit envoie à l'API
   ↓
5. API analyse avec InsightFace → Retourne résultat
   ↓
6. Streamlit affiche le résultat à l'utilisateur
```

---

## Installation et utilisation

### Prérequis

```bash
pip install -r requirements.txt 
```

### Lancement

```bash
python run.py
```

L'interface s'ouvrira automatiquement dans votre navigateur à l'adresse :
- **Interface** : http://localhost:8501
- **API** : http://localhost:8000

---

## Points forts de cette architecture

**Séparation frontend/backend** : Code modulaire et maintenable

**API réutilisable** : Peut servir d'autres clients (mobile, web, etc.)

**Chargement asynchrone** : Interface accessible immédiatement pendant le chargement du modèle

**Protection anti-crash** : Gestion complète des erreurs réseau et timeouts

**Scalable** : Facile d'ajouter de nouveaux endpoints ou fonctionnalités

**Interface intuitive** : Navigation simple entre les pages

---

## Sécurités implémentées

- **Attente API** : L'interface attend que l'API soit disponible avant d'envoyer des requêtes
- **Attente modèle** : Si le modèle n'est pas prêt, l'interface attend automatiquement
- **Timeouts** : Protection contre les blocages infinis (30s pour l'API, 60s pour le modèle)
- **Gestion d'erreurs** : Messages clairs en cas de problème

---

## Paramètres

- **Seuil de reconnaissance** : 0.35 (configurable dans `const.py`)
- **Taille de détection** : 640x640 pixels
- **Modèle** : buffalo_l (InsightFace)
- **Similarité** : Cosinus

---

## Technologies utilisées

- **FastAPI** : Framework web asynchrone pour l'API
- **Streamlit** : Framework pour l'interface web
- **InsightFace** : Modèle de reconnaissance faciale
- **OpenCV** : Traitement d'images
- **NumPy** : Calculs vectoriels

---

## Notes

- Le modèle InsightFace se télécharge automatiquement au premier lancement
- La base de données est créée automatiquement lors du premier enrôlement
- L'interface peut être utilisée immédiatement, même pendant le chargement du modèle
