# Système de Reconnaissance Faciale

Projet de reconnaissance faciale utilisant InsightFace avec une architecture modulaire séparée pour l'apprentissage et la reconnaissance.

## Architecture

```
Reconaissance_Facial/
├── const.py                        # Configuration globale
├── utils.py                        # Fonctions communes pour les UIs
├── api_utils.py                    # Fonctions communes pour les APIs
├── base_donnees_visages.json       # Base de données
├── requirements.txt
├── README.md
├── apprentissage/
│   ├── api_apprentissage.py       # API d'enrôlement (port 8000)
│   ├── ui_apprentissage.py        # Interface d'enrôlement
│   └── run_apprentissage.py       # Lance l'apprentissage
└── reconaissance/
    ├── api_reconnaissance.py      # API de reconnaissance (port 8001)
    ├── ui_reconnaissance.py       # Interface de reconnaissance
    └── run_reconnaissance.py      # Lance la reconnaissance
```

### Architecture Modulaire

- **APIs séparées** : 
  - Apprentissage (port 8000) : Enrôlement de nouveaux visages
  - Reconnaissance (port 8001) : Identification de visages
- **Interfaces dédiées** : Une interface pour chaque fonctionnalité
- **Modèle IA** : InsightFace (buffalo_l) optimisé (320x320)
- **Code partagé** : Fonctions communes dans `utils.py` et `api_utils.py`

---

## 📁 Description des fichiers

### Fichiers communs

#### `const.py` - Configuration

**Rôle** : Constantes partagées entre tous les modules

```python
DB_FILE = "base_donnees_visages.json"
SEUIL_RECONNAISSANCE = 0.35

# API Apprentissage (port 8000)
API_URL_ENROLL = "http://127.0.0.1:8000/enroll"
API_URL_STATUS_APPRENTISSAGE = "http://127.0.0.1:8000/status"

# API Reconnaissance (port 8001)
API_URL_RECO = "http://127.0.0.1:8001/recognize"
API_URL_STATUS_RECONNAISSANCE = "http://127.0.0.1:8001/status"
```

#### `utils.py` - Fonctions communes pour les UIs

**Rôle** : Fonctions partagées par les interfaces Streamlit

- `attendre_api_et_modele(api_url_status)` : Attend que l'API soit prête
- `appeler_api(url, files, params, api_url_status)` : Appelle l'API avec gestion d'erreurs

#### `api_utils.py` - Fonctions communes pour les APIs

**Rôle** : Fonctions partagées par les APIs FastAPI

- `charger_modele()` : Charge le modèle InsightFace
- `get_model()` / `is_model_ready()` / `get_model_error()` : Gestion du modèle
- `load_bd()` : Charge la base de données avec cache
- `save_vector_db()` : Sauvegarde un vecteur facial
- `redimensionner_image()` : Optimise la taille de l'image
- `similarite_cosinus()` : Calcule la similarité entre vecteurs
- `reconnaitre()` : Identifie un visage dans la base

---

### Module Apprentissage

#### `api_apprentissage.py` - API d'enrôlement

**Rôle** : API REST pour enregistrer de nouveaux visages

- **Port** : 8000
- **Modèle IA** : InsightFace (chargement asynchrone)

**Endpoints disponibles** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/status` | GET | Statut du modèle (loading/ready/error) |
| `/enroll` | POST | Enrôler un nouveau visage (param: prenom, force_enroll) |

**Fonctionnalités** :
- Détection de doublons (vérifie si le visage existe déjà)
- Ré-enrôlement possible avec `force_enroll=True`
- Optimisation d'image avant traitement

#### `ui_apprentissage.py` - Interface d'enrôlement

**Rôle** : Interface web pour ajouter des personnes

- **Framework** : Streamlit
- **Communication** : HTTP requests vers l'API (port 8000)

**Fonctionnalités** :
- Capture photo via webcam
- Saisie du prénom
- Détection automatique des doublons
- Proposition de ré-enrôlement pour améliorer la précision

#### `run_apprentissage.py` - Lanceur

**Rôle** : Lance le système d'apprentissage

```bash
python apprentissage/run_apprentissage.py
```

- Démarre l'API d'apprentissage (port 8000)
- Démarre l'interface Streamlit

---

### Module Reconnaissance

#### `api_reconnaissance.py` - API de reconnaissance

**Rôle** : API REST pour identifier des visages

- **Port** : 8001
- **Modèle IA** : InsightFace (chargement asynchrone)

**Endpoints disponibles** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/status` | GET | Statut du modèle (loading/ready/error) |
| `/recognize` | POST | Identifier un visage |

**Fonctionnalités** :
- Identification avec score de confiance
- Utilisation du cache pour la base de données
- Optimisation d'image avant traitement

#### `ui_reconnaissance.py` - Interface de reconnaissance

**Rôle** : Interface web pour identifier des personnes

- **Framework** : Streamlit
- **Communication** : HTTP requests vers l'API (port 8001)

**Fonctionnalités** :
- Capture photo via webcam
- Affichage du nom identifié et du score de confiance
- Stockage du résultat dans `session_state`

#### `run_reconnaissance.py` - Lanceur

**Rôle** : Lance le système de reconnaissance

```bash
python reconaissance/run_reconnaissance.py
```

- Démarre l'API de reconnaissance (port 8001)
- Démarre l'interface Streamlit

---

### Base de données

#### `base_donnees_visages.json`

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

### Enrôlement (Apprentissage)

```
1. run_apprentissage.py démarre
   ↓
2. API Apprentissage (port 8000) démarre → Modèle charge en thread
   ↓
3. Streamlit démarre → Interface visible immédiatement
   ↓
4. User saisit prénom + prend photo → Streamlit envoie à l'API
   ↓
5. API vérifie si visage existe déjà dans la base
   ↓
6. Si nouveau → Enregistre | Si existant → Propose ré-enrôlement
   ↓
7. Streamlit affiche confirmation
```

### Reconnaissance

```
1. run_reconnaissance.py démarre
   ↓
2. API Reconnaissance (port 8001) démarre → Modèle charge en thread
   ↓
3. Streamlit démarre → Interface visible immédiatement
   ↓
4. User prend photo → Streamlit envoie à l'API
   ↓
5. API analyse avec InsightFace → Compare avec base de données
   ↓
6. Retourne identité + score de confiance
   ↓
7. Streamlit affiche le résultat
```

---

## Installation et utilisation

### Prérequis

```bash
pip install -r requirements.txt 
```

### Lancement

**Pour l'apprentissage (enrôlement)** :
```bash
python apprentissage/run_apprentissage.py
```
- Interface : http://localhost:8501
- API : http://localhost:8000

**Pour la reconnaissance** :
```bash
python reconaissance/run_reconnaissance.py
```
- Interface : http://localhost:8501
- API : http://localhost:8001

**Note** : Les deux systèmes peuvent fonctionner simultanément car ils utilisent des ports différents.

---

## Points forts de cette architecture

✅ **Séparation complète** : Apprentissage et reconnaissance sont indépendants

✅ **Code réutilisable** : Fonctions communes dans `utils.py` et `api_utils.py`

✅ **APIs indépendantes** : Peuvent servir plusieurs clients simultanément

✅ **Optimisations** : 
   - Cache de la base de données
   - Redimensionnement d'images automatique
   - Détection de modèle de 640x640 à 320x320 (4x plus rapide)

✅ **Expérience utilisateur** : 
   - Interface accessible immédiatement
   - Détection de doublons lors de l'enrôlement
   - Proposition de ré-enrôlement pour améliorer la précision

✅ **Scalable** : Facile d'ajouter de nouveaux modules ou fonctionnalités

✅ **Maintenance simplifiée** : Code mutualisé, modifications centralisées

---

## Sécurités implémentées

- ✅ **Attente API** : L'interface attend que l'API soit disponible
- ✅ **Attente modèle** : Attente automatique du chargement du modèle
- ✅ **Timeouts** : Protection contre les blocages (30s API, 60s modèle)
- ✅ **Gestion d'erreurs** : Messages clairs et reconnexion automatique
- ✅ **Détection de doublons** : Évite les enregistrements multiples
- ✅ **Cache intelligent** : Recharge la base uniquement si modifiée

---

## Paramètres

- **Seuil de reconnaissance** : 0.35 (configurable dans `const.py`)
- **Taille de détection** : 320x320 pixels (optimisé pour la vitesse)
- **Taille max image** : 640 pixels (redimensionnement automatique)
- **Modèle** : buffalo_l (InsightFace)
- **Similarité** : Cosinus
- **Ports** : 8000 (apprentissage), 8001 (reconnaissance)

---

## Technologies utilisées

- **FastAPI** : Framework web asynchrone pour les APIs
- **Streamlit** : Framework pour les interfaces web
- **InsightFace** : Modèle de reconnaissance faciale state-of-the-art
- **OpenCV** : Traitement d'images
- **NumPy** : Calculs vectoriels et optimisations

---

## Avantages de la séparation Apprentissage/Reconnaissance

### Performance
- Chaque API charge son propre modèle indépendamment
- Pas de conflit de ressources
- Optimisations spécifiques à chaque tâche

### Sécurité
- L'apprentissage peut être isolé en production
- Droits d'accès différents possibles
- Logs séparés pour audit

### Scalabilité
- Possibilité de déployer sur des serveurs différents
- Équilibrage de charge indépendant
- Mise à jour sans interruption de service

### Développement
- Équipes peuvent travailler indépendamment
- Tests isolés plus faciles
- Déploiement progressif possible

---

## Notes

- Le modèle InsightFace se télécharge automatiquement au premier lancement
- La base de données est créée automatiquement lors du premier enrôlement
- Les interfaces peuvent être utilisées immédiatement, même pendant le chargement des modèles
- Les fonctions communes sont dans `utils.py` (UI) et `api_utils.py` (API)
- La détection de doublons lors de l'enrôlement évite les erreurs d'enregistrement
