# Guide: Sauvegarder et Réutiliser les Modèles ML Fine-Tunés

## Objectif
Entraîner et fine-tuner les modèles ML une seule fois dans `analyse_copy.ipynb`, puis les réutiliser dans `analytics.py` sans réentraîner à chaque démarrage.

## Architecture

```
analyse_copy.ipynb (Notebook)
    ↓ (Fine-tuning des modèles)
    ↓
trained_models.pkl (Sauvegarde)
    ↓ (Chargement)
    ↓
analytics.py (API FastAPI)
```

## Workflow

### 1. Dans `analyse_copy.ipynb` - Entraînement et Fine-Tuning

Après avoir entraîné et fine-tuné tous vos modèles (4 classifeurs + 1 regresseur):

#### Option A: Sauvegarder manuellement depuis dicts structurés

```python
import pickle
import os

# Après fine-tuning, créez les dictionnaires:
best_models = {
    "client_risque": votre_modele_1,
    "installation_reussie_encoded": votre_modele_2,
    "client_satisfait_encoded": votre_modele_3,
    "client_a_reclame_encoded": votre_modele_4,
    "Duree_installation_minutes": votre_regresseur,
}

best_model_names = {
    "client_risque": "Random Forest",
    "installation_reussie_encoded": "XGBoost",
    # ... etc
}

selected_features = {
    "client_risque": ["feature1", "feature2", ...],
    # ... etc
}

X_test_dict = {
    "client_risque": X_test_1,
    # ... etc
}

y_test_dict = {
    "client_risque": y_test_1,
    # ... etc
}

explainers = {
    "client_risque": shap_explainer_1,
    # ... ou None si pas disponible
}

shap_values_dict = {
    "client_risque": shap_vals_1,
    # ... ou None si pas disponible
}

results_dfs = {
    "client_risque": results_dataframe_1,
    # ... avec colonnes: Modèle, Accuracy, F1-Score, ROC-AUC, etc
}

# Puis exécutez la cellule de sauvegarde du notebook
```

#### Option B: Utiliser directement `_train_all_models` d'analytics.py

```python
from app.services.analytics import _train_all_models

# Où df est votre DataFrame complèt avec toutes les features
trained_models_bundle = _train_all_models(df)

# Sauvegarder
models_save_path = os.path.join(os.path.dirname(__file__), "trained_models.pkl")
with open(models_save_path, "wb") as f:
    pickle.dump(trained_models_bundle, f)

print(f"✅ Modèles sauvegardés: {models_save_path}")
```

### 2. Format du Bundle Sauvegardé

Le fichier `trained_models.pkl` contient:

```python
{
    "client_risque": {
        "model": <modèle entraîné>,
        "model_name": "Random Forest",
        "features": ["feature1", "feature2", ...],
        "X_test": <données test>,
        "y_test": <cibles test>,
        "explainer": <SHAP TreeExplainer ou None>,
        "shap_values": <valeurs SHAP pré-calculées ou None>,
        "results_df": <DataFrame avec métriques>,
        "task": "classification",
    },
    "installation_reussie_encoded": { ... },
    "client_satisfait_encoded": { ... },
    "client_a_reclame_encoded": { ... },
    "Duree_installation_minutes": {
        "task": "regression",
        ...
    }
}
```

### 3. Dans `analytics.py` - Chargement Automatique

Le système de cache dans `_get_models()` fonctionne déjà:

```python
def _get_models(db: Session) -> tuple[pd.DataFrame, dict]:
    global _MODEL_CACHE, _MODEL_CACHE_SIZE
    rows = _rows(db)
    
    with _MODEL_CACHE_LOCK:
        # 1. Vérifier cache en mémoire (session actuelle)
        if _MODEL_CACHE is not None and len(rows) == _MODEL_CACHE_SIZE:
            return _build_dataframe(rows), _MODEL_CACHE

        # 2. Charger depuis fichier pickle si disponible
        if os.path.exists(MODEL_PATH):  # ← Charge votre trained_models.pkl
            try:
                with open(MODEL_PATH, "rb") as f:
                    _MODEL_CACHE = pickle.load(f)
                _MODEL_CACHE_SIZE = len(rows)
                return _build_dataframe(rows), _MODEL_CACHE
            except Exception:
                _MODEL_CACHE = None

        # 3. Sinon, réentraîner (fallback)
        df = _build_dataframe(rows)
        _MODEL_CACHE = _train_all_models(df)
        _MODEL_CACHE_SIZE = len(rows)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(_MODEL_CACHE, f)
        return df, _MODEL_CACHE
```

**Résultat:**
- ✅ Première exécution: Charge depuis `trained_models.pkl`
- ✅ Même données: Utilise le cache en mémoire
- ✅ Données changent: Réentraîne automatiquement
- ⏱️  AUCUN réentraînement inutile

### 4. Localisation du Fichier

```
backend/app/services/
├── analytics.py
├── analyse_copy.ipynb
├── trained_models.pkl  ← ICI (créé après sauvegarde)
└── ...autres fichiers
```

`MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_models.pkl")`

## Checklist

- [ ] Fine-tuner les 5 modèles dans `analyse_copy.ipynb`
- [ ] Créer les dictionnaires structurés OU utiliser `_train_all_models`
- [ ] Exécuter la cellule de sauvegarde
- [ ] Vérifier: fichier `trained_models.pkl` créé dans `backend/app/services/`
- [ ] Redémarrer l'API FastAPI
- [ ] Vérifier: Les modèles se chargent sans messages de réentraînement

## Dépannage

| Problème | Solution |
|----------|----------|
| "NameError: best_models not defined" | Vérifier que les dicts existent après fine-tuning |
| Fichier `trained_models.pkl` non créé | Vérifier le chemin: `backend/app/services/` |
| Les modèles se réentraînent quand même | Vérifier que `trained_models.pkl` existe et est valide |
| Erreur "Can't pickle" | Certains modèles SHAP ne peuvent pas être sérialisés - mettre `explainer: None` |

## Logs

Quand `_get_models` s'exécute:
```
✅ Les modèles chargés depuis trained_models.pkl (rapide)
⏳ Les modèles réentraînent (lent, seulement si données changent)
```

## Variables d'Environnement

Aucune configuration nécessaire - tout est automatique!

## Bonus: Regenerer les Modèles

Si vous voulez forcer un réentraînement:
```bash
# Supprimer le fichier cache
rm backend/app/services/trained_models.pkl

# Redémarrer l'API - elle va réentraîner automatiquement
```
