# Système de Reconnaissance Faciale

Projet de reconnaissance faciale utilisant InsightFace avec une architecture modulaire séparée pour l'apprentissage et la reconnaissance.

## 🆕 Nouveauté : Enrôlement Multi-Photos

Le système utilise désormais un **enrôlement en 3 photos** pour améliorer la robustesse de la reconnaissance :
- 📷 Photo 1 : Visage de **face**
- 📷 Photo 2 : Visage tourné vers la **gauche** (~30°)
- 📷 Photo 3 : Visage tourné vers la **droite** (~30°)

Cette approche permet de capturer plusieurs angles du visage, améliorant significativement la précision sans changer de modèle.

## Architecture

```
Reconaissance_Facial/
├── const.py                        # Configuration globale
├── base_donnees_visages.json       # Base de données des embeddings
├── requirements.txt
├── README.md
├── utils/
│   ├── ui_utils.py                # Fonctions communes pour les UIs
│   └── api_utils.py               # Fonctions communes pour les APIs
├── apprentissage/
│   ├── api_apprentissage.py       # API d'enrôlement (port 8000)
│   ├── ui_apprentissage.py        # Interface d'enrôlement multi-photos
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
- **Modèle IA** : InsightFace (buffalo_l)
- **Code partagé** : Fonctions communes dans `utils/`

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

#### `utils/ui_utils.py` - Fonctions communes pour les UIs

**Rôle** : Fonctions partagées par les interfaces Streamlit

- `attendre_api_et_modele(api_url_status)` : Attend que l'API soit prête
- `appeler_api(url, files, params, api_url_status)` : Appelle l'API avec gestion d'erreurs

#### `utils/api_utils.py` - Fonctions communes pour les APIs

**Rôle** : Fonctions partagées par les APIs FastAPI

- `charger_modele()` : Charge le modèle InsightFace
- `get_model()` / `is_model_ready()` / `get_model_error()` : Gestion du modèle
- `load_bd()` : Charge la base de données avec cache
- `save_vector_db()` : Sauvegarde un vecteur facial
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
- Support multi-photos (3 embeddings par utilisateur)

#### `ui_apprentissage.py` - Interface d'enrôlement Multi-Photos

**Rôle** : Interface web pour ajouter des personnes avec 3 photos guidées

- **Framework** : Streamlit
- **Communication** : HTTP requests vers l'API (port 8000)

**Processus d'enrôlement en 3 étapes** :

| Étape | Instruction | Description |
|-------|-------------|-------------|
| 1/3 | Visage de FACE | Regarder directement la caméra |
| 2/3 | Visage vers la GAUCHE | Tourner la tête ~30° vers la gauche |
| 3/3 | Visage vers la DROITE | Tourner la tête ~30° vers la droite |

**Fonctionnalités** :
- ✅ Capture guidée étape par étape
- ✅ Barre de progression visuelle (0/3 → 3/3)
- ✅ Détection automatique des doublons (1ère photo uniquement)
- ✅ Proposition de ré-enrôlement pour améliorer la précision
- ✅ Bouton "Recommencer" pour réinitialiser le processus
- ✅ Résumé final avec confirmation

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

**Rôle** : Stockage des vecteurs faciaux (embeddings)

Avec l'enrôlement multi-photos, chaque utilisateur possède **3 entrées** :

```json
[
  {
    "identifiant": "Jean",
    "vecteur": [0.123, -0.456, ...]   // Photo face
  },
  {
    "identifiant": "Jean",
    "vecteur": [0.234, -0.567, ...]   // Photo gauche
  },
  {
    "identifiant": "Jean",
    "vecteur": [0.345, -0.678, ...]   // Photo droite
  },
  {
    "identifiant": "Marie",
    "vecteur": [0.321, -0.654, ...]   // Photo face
  }
  // ... etc
]
```

Lors de la reconnaissance, le système compare le visage à **tous les embeddings** et retourne le meilleur score, améliorant ainsi la robustesse.

---

## 🔄 Flux de fonctionnement

### Enrôlement Multi-Photos (Apprentissage)

```
1. run_apprentissage.py démarre
   ↓
2. API Apprentissage (port 8000) démarre → Modèle charge en thread
   ↓
3. Streamlit démarre → Interface visible immédiatement
   ↓
4. User saisit prénom
   ↓
5. ÉTAPE 1/3 : Capture photo FACE
   ├─ Envoi à l'API → Vérification doublon
   ├─ Si nouveau → Enregistre embedding #1
   └─ Si existant → Propose ré-enrôlement
   ↓
6. ÉTAPE 2/3 : Capture photo GAUCHE
   └─ Envoi à l'API → Enregistre embedding #2
   ↓
7. ÉTAPE 3/3 : Capture photo DROITE
   └─ Envoi à l'API → Enregistre embedding #3
   ↓
8. ✅ Enrôlement complet (3 embeddings pour 1 utilisateur)
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

✅ **Enrôlement multi-angles** : 3 photos pour une meilleure robustesse

✅ **Séparation complète** : Apprentissage et reconnaissance sont indépendants

✅ **Code réutilisable** : Fonctions communes dans `utils/`

✅ **APIs indépendantes** : Peuvent servir plusieurs clients simultanément

✅ **Expérience utilisateur** : 
   - Interface guidée étape par étape
   - Barre de progression visuelle
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

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Seuil de reconnaissance | 0.35 | Configurable dans `const.py` |
| Taille de détection | 640x640 | Résolution du modèle |
| Photos par enrôlement | 3 | Face, Gauche, Droite |
| Modèle | buffalo_l | InsightFace |
| Similarité | Cosinus | Méthode de comparaison |
| Port apprentissage | 8000 | API d'enrôlement |
| Port reconnaissance | 8001 | API de reconnaissance |

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
- Les fonctions communes sont dans `utils/ui_utils.py` (UI) et `utils/api_utils.py` (API)
- La détection de doublons lors de l'enrôlement évite les erreurs d'enregistrement
- **Chaque utilisateur génère 3 embeddings** (face, gauche, droite) pour une meilleure reconnaissance
- La reconnaissance compare automatiquement avec tous les embeddings et retourne le meilleur match
