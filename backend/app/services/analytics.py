from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import os
import pickle
from collections import defaultdict
from datetime import datetime, timedelta
from types import SimpleNamespace
import time
from typing import Iterable, Any
from threading import Lock, Thread
from category_encoders import TargetEncoder
import numpy as np
import pandas as pd
from plotly import graph_objects as go
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
try:
    from pmdarima import auto_arima
except Exception:
    auto_arima = None
from sklearn.model_selection import train_test_split
from sqlalchemy import func, select
from sqlalchemy.orm import Session, load_only

from app.db.models import InstallationProduitCNI

# Lazy-loaded ML libraries (only imported when needed)
SHAP_AVAILABLE = False
_ML_IMPORTS_CACHED = {}

# ════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

GOUVERNORATS_RISQUE = {"Gafsa", "Jendouba", "Kasserine", "Médenine", "Tataouine"}

METROPOLITAINE = {
    "Tunis", "Ariana", "Ben Arous", "Manouba",
    "Sfax", "Sousse", "Monastir", "Nabeul", "Bizerte",
}
MIXTE = {
    "Mahdia", "Kairouan", "Gabès", "Zaghouan",
    "Béja", "Siliana", "Le Kef", "Tozeur", "Gafsa",
}
RURALE = {"Jendouba", "Kasserine", "Sidi Bouzid", "Médenine", "Tataouine", "Kébili"}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_models.pkl")

# ════════════════════════════════════════════════════════════════════════════
# CACHING
# ════════════════════════════════════════════════════════════════════════════
_ANALYSIS_CACHE = {}
_ANALYSIS_CACHE_TTL_SECONDS = 300
_ANALYSIS_CACHE_VERSION = 2


def _analysis_signature(db: Session) -> tuple[int, str | None, str | None]:
    row_count, latest_installation, latest_product = db.execute(
        select(
            func.count(InstallationProduitCNI.id),
            func.max(InstallationProduitCNI.date_installation),
            func.max(InstallationProduitCNI.nom_produit),
        )
    ).one()
    latest_date = latest_installation.isoformat() if latest_installation is not None else None
    return int(row_count or 0), latest_date, latest_product


def clear_target_analysis_cache() -> None:
    """Clear cached target analysis results."""
    _ANALYSIS_CACHE.clear()

# ════════════════════════════════════════════════════════════════════════════
# HELPERS JSON
# ════════════════════════════════════════════════════════════════════════════

def _figure_json(fig: go.Figure) -> dict:
    return fig.to_plotly_json()


def _to_serializable(obj):
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_to_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    elif isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj
    
# ════════════════════════════════════════════════════════════════════════════
# BUILD DATAFRAME 
# ════════════════════════════════════════════════════════════════════════════
#Access data from database
def _rows(db: Session) -> list[InstallationProduitCNI]:
    stmt = select(
        InstallationProduitCNI.id.label("id"),
        InstallationProduitCNI.nom_produit.label("nom_produit"),
        InstallationProduitCNI.version_produit.label("version_produit"),
        InstallationProduitCNI.date_installation.label("date_installation"),
        InstallationProduitCNI.gouvernorat.label("gouvernorat"),
        InstallationProduitCNI.id_client.label("id_client"),
        InstallationProduitCNI.type_client.label("type_client"),
        InstallationProduitCNI.systeme_exploitation_poste.label("systeme_exploitation_poste"),
        InstallationProduitCNI.installation_reussie.label("installation_reussie"),
        InstallationProduitCNI.nombre_essais_installation.label("nombre_essais_installation"),
        InstallationProduitCNI.client_a_reclame.label("client_a_reclame"),
        InstallationProduitCNI.nombre_reclamations_client.label("nombre_reclamations_client"),
        InstallationProduitCNI.client_satisfait.label("client_satisfait"),
        InstallationProduitCNI.remarques.label("remarques"),
        InstallationProduitCNI.technicien_id.label("technicien_id"),
        InstallationProduitCNI.duree_installation_minutes.label("duree_installation_minutes"),
        InstallationProduitCNI.debit_reseau_mbps.label("debit_reseau_mbps"),
        InstallationProduitCNI.taille_site_postes.label("taille_site_postes"),
        InstallationProduitCNI.mode_installation.label("mode_installation"),
        InstallationProduitCNI.tentative_installation_weekend.label("tentative_installation_weekend"),
        InstallationProduitCNI.version_precedente.label("version_precedente"),
    )
    rows = db.execute(stmt).mappings().all()
    return [SimpleNamespace(**dict(row)) for row in rows if row is not None]

def _build_dataframe(rows: list[InstallationProduitCNI]) -> pd.DataFrame:
    records = []
    for r in rows:
        records.append({
            "Id_Client":                     r.id_client,
            "date_installation":             r.date_installation,
            "Nom_produit":                   r.nom_produit,
            "Gouvernorat":                   r.gouvernorat,
            "Type_client":                   r.type_client,
            "Systeme_exploitation_poste":    r.systeme_exploitation_poste,
            "version_produit":               r.version_produit,
            "Version_precedente":            r.version_precedente,
            "Taille_site_postes":            r.taille_site_postes,
            "Debit_reseau_Mbps":             r.debit_reseau_mbps,
            "Duree_installation_minutes":    r.duree_installation_minutes,
            "nombre_essais_installation":    r.nombre_essais_installation,
            "nombre_reclamations_client":    r.nombre_reclamations_client,
            "Mode_installation":             r.mode_installation,
            "Tentative_installation_weekend": r.tentative_installation_weekend,
            "Technicien_ID":                 r.technicien_id,
            "installation_reussie":          r.installation_reussie,
            "client_a_reclame":              r.client_a_reclame,
            "client_satisfait":              r.client_satisfait,
            "Remarques":                     r.remarques,
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df["date_installation"] = pd.to_datetime(df["date_installation"], errors="coerce")
    version_numeric = df["version_produit"].astype(str).str.extract(r"(\d+(?:\.\d+)?)", expand=False)
    df["version_produit_num"] = pd.to_numeric(version_numeric, errors="coerce").fillna(0.0)

    month_ecart = (
        df.groupby(df["date_installation"].dt.to_period("M"))["version_produit_num"]
        .agg(lambda x: x.max() - x.min())
        .to_dict()
    )
    version_ecart_by_month = {str(k): v for k, v in month_ecart.items()}

    for i, row_orm in enumerate(rows):
        imputed = _impute_remarque(row_orm, version_ecart_by_month)
        if not df.at[i, "Remarques"] or not str(df.at[i, "Remarques"]).strip():
            df.at[i, "Remarques"] = imputed

    for col in ["installation_reussie", "client_a_reclame", "client_satisfait",
                "Tentative_installation_weekend"]:
        df[col + "_encoded"] = df[col].map({"oui": 1, "non": 0}).fillna(0).astype(int)

    df["cat_taille"]         = df["Taille_site_postes"].apply(_cat_taille)
    df["cat_debit"]          = df["Debit_reseau_Mbps"].apply(_cat_debit)
    df["zone_urbanisation"]  = df["Gouvernorat"].apply(_zone_urbanisation)

    flags = df["Remarques"].apply(_remarques_flags).apply(pd.Series)
    df = pd.concat([df, flags], axis=1)

    df["annee"]      = df["date_installation"].dt.year
    df["jour_semaine"] = df["date_installation"].dt.dayofweek
    df["mois"]       = df["date_installation"].dt.to_period("M").astype(str)
    df["mois_num"]   = df["date_installation"].dt.month

    df["upgrade"] = (
        df["version_produit_num"] == df["version_produit_num"].max()
    ).astype(int)

    df["score_risque"] = [_score_risque(r) for r in rows]
    df["client_risque"] = (df["score_risque"] >= 3).astype(int)

    ohe_cols = ["Nom_produit", "Type_client", "Mode_installation",
                "cat_taille", "cat_debit", "zone_urbanisation"]
    df = pd.get_dummies(df, columns=ohe_cols, drop_first=True)

    return df

# ════════════════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING HELPERS
# ════════════════════════════════════════════════════════════════════════════
def _impute_remarque(
    row: InstallationProduitCNI,
    version_ecart_by_month: dict[str, float],
) -> str | None:
    if row.remarques and row.remarques.strip():
        return row.remarques

    # Règle 0
    if _as_binary(row.installation_reussie) == 1 and _as_binary(row.client_satisfait) == 1:
        return "Aucune"

    month_key = row.date_installation.strftime("%Y-%m") if row.date_installation else ""

    # Règle 1
    if row.nom_produit == "MAKATIB" and row.taille_site_postes >= 26:
        return "manque espace disque"

    # Règle 2
    if version_ecart_by_month.get(month_key, 0) > 1:
        return "version incompatible"

    # Règle 3
    if (
        row.type_client == "EPNA"
        and row.mode_installation == "Télémaintenance"
        and row.gouvernorat in GOUVERNORATS_RISQUE
    ):
        return "Problème adressage ip"

    # Règle 4
    os_ = str(row.systeme_exploitation_poste or "")
    try:
        ver = float(row.version_produit)
    except (TypeError, ValueError):
        ver = 0.0
    if os_ in {"Unknown", "WindowsXP"} and ver >= 2.0:
        return "erreur configuration poste"

    # Règle 5
    if ver >= 2.0 and row.gouvernorat in GOUVERNORATS_RISQUE:
        return "poste obsolète"

    # Règle 6
    if row.debit_reseau_mbps <= 8:
        return np.random.choice(["connexion serveur lente", "problème réseau"])

    return "Aucune"

def _as_binary(value: str | None) -> int:
    return 1 if str(value).lower() == "oui" else 0

def _cat_taille(x: float) -> str:
    if x <= 10:
        return "petit"
    elif x <= 20:
        return "moyen"
    return "grand"


def _cat_debit(x: float) -> str:
    if x < 5:
        return "faible"
    elif x < 20:
        return "moyen"
    return "bon"

def _zone_urbanisation(gouvernorat: str) -> str:
    if gouvernorat in METROPOLITAINE:
        return "metropolitaine"
    elif gouvernorat in MIXTE:
        return "mixte"
    elif gouvernorat in RURALE:
        return "rurale"
    return "inconnu"


def _score_risque(row: InstallationProduitCNI) -> int:
    score = 0
    if row.debit_reseau_mbps < 5:
        score += 1
    if row.nombre_essais_installation > 2:
        score += 1
    if row.duree_installation_minutes > 120:
        score += 1
    if row.systeme_exploitation_poste in {"windowsxp","Win7", "Win8", "Windows 2012 Server", "Windows 2016 Server"}:
        score += 1
    if row.nom_produit == "GRB":
        score += 1
    if row.gouvernorat in GOUVERNORATS_RISQUE:
        score += 1
    if row.taille_site_postes > 15:
        score += 1
    if row.version_produit and str(row.version_produit).startswith(("1.", "2.", "3.")):
        score += 1
    return score


def _client_risque(row: InstallationProduitCNI) -> int:
    return 1 if _score_risque(row) >= 3 else 0


def _remarques_flags(remarque: str | None) -> dict[str, int]:
    r = str(remarque or "")
    return {
        "pb_reseau":        int(bool(pd.Series([r]).str.contains("réseau|connexion|serveur", case=False, na=False)[0])),
        "pb_configuration": int(bool(pd.Series([r]).str.contains("configuration|adresse|ip",  case=False, na=False)[0])),
        "pb_materiel":      int(bool(pd.Series([r]).str.contains("disque|poste|obsolète",      case=False, na=False)[0])),
        "pb_version":       int(bool(pd.Series([r]).str.contains("version|incompatible",       case=False, na=False)[0])),
        "pb_aucun":         int(bool(pd.Series([r]).str.contains("Aucun|Aucune",               case=False, na=False)[0])),
    }

def _target_encoding(X_train, X_test, df_full, target):
    y_train = df_full.loc[X_train.index, target]
    y_test  = df_full.loc[X_test.index, target]
    cols = ["Systeme_exploitation_poste", "version_produit"] if "Systeme_exploitation_poste" in X_train.columns else []
    cols = [c for c in cols if c in X_train.columns]
    if cols:
        encoder = TargetEncoder(cols=cols)
        X_train = X_train.copy()
        X_test  = X_test.copy()
        X_train[cols] = encoder.fit_transform(X_train[cols], y_train)
        X_test[cols]  = encoder.transform(X_test[cols])
    return X_train, X_test, y_train, y_test

def _feature_selection(X, y, task="classification", k=15, seuil=0.01):
    if task == "classification":
        from sklearn.feature_selection import mutual_info_classif
        mi = mutual_info_classif(X, y, random_state=42)
    else:
        from sklearn.feature_selection import mutual_info_regression
        mi = mutual_info_regression(X, y, random_state=42)
    mi_df = pd.DataFrame({"feature": X.columns, "MI": mi}).sort_values("MI", ascending=False)
    retenues = mi_df[mi_df["MI"] >= seuil].head(k)
    return retenues["feature"].tolist(), mi_df

# ════════════════════════════════════════════════════════════════════════════
# Modelisation HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _get_classifieurs():
    if "classifieurs" not in _ML_IMPORTS_CACHED:
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.svm import SVC
        from sklearn.tree import DecisionTreeClassifier
        from xgboost import XGBClassifier

        _ML_IMPORTS_CACHED["classifieurs"] = {
            "Logistic Regression": LogisticRegression,
            "Decision Tree":       DecisionTreeClassifier,
            "Random Forest":       RandomForestClassifier,
            "Gradient Boosting":   GradientBoostingClassifier,
            "XGBoost":             XGBClassifier,
            "KNN":                 KNeighborsClassifier,
            "SVM":                 SVC,
        }
    return {
        "Logistic Regression": _ML_IMPORTS_CACHED["classifieurs"]["Logistic Regression"](max_iter=1000, random_state=42),
        "Decision Tree":       _ML_IMPORTS_CACHED["classifieurs"]["Decision Tree"](random_state=42),
        "Random Forest":       _ML_IMPORTS_CACHED["classifieurs"]["Random Forest"](n_estimators=100, random_state=42),
        "Gradient Boosting":   _ML_IMPORTS_CACHED["classifieurs"]["Gradient Boosting"](random_state=42),
        "XGBoost":             _ML_IMPORTS_CACHED["classifieurs"]["XGBoost"](eval_metric="logloss", random_state=42),
        "KNN":                 _ML_IMPORTS_CACHED["classifieurs"]["KNN"](),
        "SVM":                 _ML_IMPORTS_CACHED["classifieurs"]["SVM"](probability=True, random_state=42),
    }

def _get_regresseurs():
    if "regresseurs" not in _ML_IMPORTS_CACHED:
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.linear_model import Lasso, LinearRegression, Ridge
        from sklearn.tree import DecisionTreeRegressor
        from xgboost import XGBRegressor

        _ML_IMPORTS_CACHED["regresseurs"] = {
            "Linear Regression": LinearRegression,
            "Ridge":             Ridge,
            "Lasso":             Lasso,
            "Decision Tree":     DecisionTreeRegressor,
            "Random Forest":     RandomForestRegressor,
            "Gradient Boosting": GradientBoostingRegressor,
            "XGBoost":           XGBRegressor,
        }
    return {
        "Linear Regression": _ML_IMPORTS_CACHED["regresseurs"]["Linear Regression"](),
        "Ridge":             _ML_IMPORTS_CACHED["regresseurs"]["Ridge"](random_state=42),
        "Lasso":             _ML_IMPORTS_CACHED["regresseurs"]["Lasso"](random_state=42),
        "Decision Tree":     _ML_IMPORTS_CACHED["regresseurs"]["Decision Tree"](random_state=42),
        "Random Forest":     _ML_IMPORTS_CACHED["regresseurs"]["Random Forest"](n_estimators=100, random_state=42),
        "Gradient Boosting": _ML_IMPORTS_CACHED["regresseurs"]["Gradient Boosting"](random_state=42),
        "XGBoost":           _ML_IMPORTS_CACHED["regresseurs"]["XGBoost"](random_state=42),
    }

def _evaluer_classifieurs(modeles, X_train, X_test, y_train, y_test):
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    
    resultats = []
    for nom, modele in modeles.items():
        try:
            modele.fit(X_train, y_train)
            y_pred  = modele.predict(X_test)
            y_proba = modele.predict_proba(X_test)[:, 1] if hasattr(modele, "predict_proba") else None
            cv = cross_val_score(modele, X_train, y_train, cv=StratifiedKFold(5), scoring="f1").mean()
            resultats.append({
                "Modèle":   nom,
                "Accuracy": accuracy_score(y_test, y_pred),
                "F1-Score": f1_score(y_test, y_pred, zero_division=0),
                "ROC-AUC":  roc_auc_score(y_test, y_proba) if y_proba is not None else None,
                "CV F1":    cv,
            })
        except Exception:
            continue
    return pd.DataFrame(resultats).sort_values("F1-Score", ascending=False)


def _evaluer_regresseurs(modeles, X_train, X_test, y_train, y_test):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import KFold, cross_val_score
    
    resultats = []
    for nom, modele in modeles.items():
        try:
            modele.fit(X_train, y_train)
            y_pred = modele.predict(X_test)
            cv = cross_val_score(modele, X_train, y_train, cv=KFold(5), scoring="r2").mean()
            resultats.append({
                "Modèle": nom,
                "R²":     r2_score(y_test, y_pred),
                "MAE":    mean_absolute_error(y_test, y_pred),
                "RMSE":   np.sqrt(mean_squared_error(y_test, y_pred)),
                "CV R²":  cv,
            })
        except Exception:
            continue
    return pd.DataFrame(resultats).sort_values("R²", ascending=False)

def _train_all_models(df: pd.DataFrame) -> dict:
    
    _ensure_shap_available()
    
    targets = [
        "installation_reussie_encoded",
        "client_satisfait_encoded",
        "Duree_installation_minutes",
        "client_risque",
        "client_a_reclame_encoded",
    ]

    drop_cols = [c for c in targets + [
        "date_installation", "Gouvernorat", "Id_Client",
        "installation_reussie", "client_a_reclame", "client_satisfait",
        "Remarques", "Technicien_ID", "Tentative_installation_weekend",
        "Version_precedente", "mois", "score_risque",
    ] if c in df.columns]

    X = df.drop(columns=drop_cols, errors="ignore")
    X_train_base, X_test_base = train_test_split(X, test_size=0.2, random_state=42)

    bundle = {}

    classif_configs = [
        ("client_risque",               "classification"),
        ("installation_reussie_encoded","classification"),
        ("client_satisfait_encoded",    "classification"),
        ("client_a_reclame_encoded",    "classification"),
    ]

    for target, task in classif_configs:
        Xtr = X_train_base.copy()
        Xte = X_test_base.copy()
        Xtr, Xte, ytr, yte = _target_encoding(Xtr, Xte, df, target)
        feats, _ = _feature_selection(Xtr, ytr, task=task, k=15)
        Xtr, Xte = Xtr[feats], Xte[feats]

        classifieurs = _get_classifieurs()
        res = _evaluer_classifieurs(classifieurs, Xtr, Xte, ytr, yte)
        best_name = res.iloc[0]["Modèle"]
        best_model = classifieurs[best_name]
        best_model.fit(Xtr, ytr)

        explainer = None
        shap_values = None
        if SHAP_AVAILABLE and hasattr(best_model, "estimators_"):
            try:
                shap = _ML_IMPORTS_CACHED.get("shap")
                explainer   = shap.TreeExplainer(best_model)
                shap_values = explainer.shap_values(Xte)
            except Exception:
                pass

        bundle[target] = {
            "model":       best_model,
            "model_name":  best_name,
            "features":    feats,
            "X_test":      Xte,
            "y_test":      yte,
            "explainer":   explainer,
            "shap_values": shap_values,
            "results_df":  res,
            "task":        "classification",
        }

    target = "Duree_installation_minutes"
    Xtr = X_train_base.copy()
    Xte = X_test_base.copy()
    Xtr, Xte, ytr, yte = _target_encoding(Xtr, Xte, df, target)
    feats, _ = _feature_selection(Xtr, ytr, task="regression", k=15)
    Xtr, Xte = Xtr[feats], Xte[feats]

    regresseurs = _get_regresseurs()
    res = _evaluer_regresseurs(regresseurs, Xtr, Xte, ytr, yte)
    best_name = res.iloc[0]["Modèle"]
    best_model = regresseurs[best_name]
    best_model.fit(Xtr, ytr)

    explainer = None
    shap_values = None
    if SHAP_AVAILABLE and hasattr(best_model, "estimators_"):
        try:
            shap = _ML_IMPORTS_CACHED.get("shap")
            explainer   = shap.TreeExplainer(best_model)
            shap_values = explainer.shap_values(Xte)
        except Exception:
            pass

    bundle[target] = {
        "model":       best_model,
        "model_name":  best_name,
        "features":    feats,
        "X_test":      Xte,
        "y_test":      yte,
        "explainer":   explainer,
        "shap_values": shap_values,
        "results_df":  res,
        "task":        "regression",
    }

    return bundle


_MODEL_CACHE: dict | None = None
_MODEL_CACHE_SIZE: int = 0
_MODEL_CACHE_LOCK = Lock()


def _get_models(db: Session) -> tuple[pd.DataFrame, dict]:
    global _MODEL_CACHE, _MODEL_CACHE_SIZE
    rows = _rows(db)
    with _MODEL_CACHE_LOCK:
        if _MODEL_CACHE is not None and len(rows) == _MODEL_CACHE_SIZE:
            return _build_dataframe(rows), _MODEL_CACHE

        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    _MODEL_CACHE = pickle.load(f)
                _MODEL_CACHE_SIZE = len(rows)
                return _build_dataframe(rows), _MODEL_CACHE
            except Exception:
                _MODEL_CACHE = None

        df = _build_dataframe(rows)
        _MODEL_CACHE = _train_all_models(df)
        _MODEL_CACHE_SIZE = len(rows)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(_MODEL_CACHE, f)
        return df, _MODEL_CACHE


# ════════════════════════════════════════════════════════════════════════════
# SHAP HELPERS
# ════════════════════════════════════════════════════════════════════════════
def _ensure_shap_available():
    global SHAP_AVAILABLE
    if not SHAP_AVAILABLE and "shap" not in _ML_IMPORTS_CACHED:
        try:
            import shap as shap_module
            _ML_IMPORTS_CACHED["shap"] = shap_module
            SHAP_AVAILABLE = True
        except ImportError:
            SHAP_AVAILABLE = False
    return _ML_IMPORTS_CACHED.get("shap", None) if SHAP_AVAILABLE else None

def _get_shap_explanation(shap_values, X, i: int, top_n: int = 3) -> list[str]:
    if shap_values is None:
        row = X.iloc[i]
        candidates = []
        for feature, value in row.items():
            try:
                numeric_value = float(value)
            except Exception:
                continue
            if numeric_value != 0:
                candidates.append((feature, abs(numeric_value), numeric_value))
        candidates.sort(key=lambda item: item[1], reverse=True)
        return [f"{feature.replace('_', ' ')} ({round(value, 2)})" for feature, _, value in candidates[:top_n]]
    vals = shap_values[1][i] if isinstance(shap_values, list) else shap_values[i]
    df_shap = pd.DataFrame({"feature": X.columns, "impact": vals})
    df_shap["abs"] = df_shap["impact"].abs()
    df_shap = df_shap.sort_values("abs", ascending=False).head(top_n)
    return [f"{row.feature.replace('_', ' ')} ({round(row.impact, 2)})" for row in df_shap.itertuples()]


def _shap_importance(shap_values, X) -> pd.DataFrame:
    if shap_values is None:
        return pd.DataFrame(columns=["feature", "importance"])
    vals = shap_values[1] if isinstance(shap_values, list) else shap_values
    importance = pd.DataFrame({
        "feature":    X.columns,
        "importance": np.abs(vals).mean(axis=0),
    }).sort_values("importance", ascending=False)
    return importance


# ════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _generer_recommandations(row: pd.Series) -> list[str]:

    recs = []
    def add(action: str) -> None:
        if action not in recs:
            recs.append(action)

    if row.get("pb_reseau", 0) == 1:
        add("Audit réseau")
        add("Audit réseau préventif")
    if row.get("cat_debit", "") == "faible" or row.get("Debit_reseau_Mbps", 99) < 5:
        add("Augmenter débit réseau")
        recs.append("Augmenter le débit réseau (< 5 Mbps détecté)")
    if row.get("pb_configuration", 0) == 1:
        add("Reconfigurer poste du client")
        add("Reconfigurer le poste du client")
    if row.get("pb_materiel", 0) == 1:
        add("Maintenance/remplacement matériel")
        add("Maintenance ou remplacement du matériel")
    if row.get("pb_version", 0) == 1 or row.get("upgrade", 1) == 0:
        add("Mettre à jour version produit")
        add("Mettre à jour la version du produit")
    if row.get("cat_taille", "") == "grand" or row.get("Taille_site_postes", 0) > 20:
        add("Le poste est tellement grand que ça complique l'installation, changer l'infrastructure du client")
        recs.append("Infrastructure volumineuse — planifier déploiement par phases")
    if row.get("zone_urbanisation", "") == "rurale" or row.get("Gouvernorat", "") in GOUVERNORATS_RISQUE:
        add("Planifier déplacement anticipé")
        recs.append("Zone difficile — anticiper déplacement sur site")
    if row.get("Tentative_installation_weekend_encoded", 0) == 1:
        recs.append("Replanifier l'installation hors weekend")
        add("Replanifier hors weekend")
    os_ = str(row.get("Systeme_exploitation_poste", ""))
    if os_ in {"WindowsXP", "Win7", "Win8", "Windows 2012 Server", "Windows 2016 Server"}:
        recs.append("Mettre à jour le système d'exploitation du poste client")
    if row.get("nombre_essais_installation", 1) > 2:
        recs.append("Technicien à assister — nombre d'essais élevé")
    return recs


def _prioriser_actions(recommandations: list[str], proba: float) -> list[dict]:
    return [
        {"action": r, "priorite": round(proba * (5 - i * 0.5), 2)}
        for i, r in enumerate(recommandations[:3])
    ]


# ════════════════════════════════════════════════════════════════════════════
# TEMPORAL KPI HELPER
# ════════════════════════════════════════════════════════════════════════════

def _kpi_temporel(rows: list[InstallationProduitCNI]) -> list[dict]:
    grouped: dict[str, list] = defaultdict(list)
    for row in rows:
        if row.date_installation:
            grouped[row.date_installation.strftime("%Y-%m")].append(row)

    temporal = []
    for month in sorted(grouped.keys()):
        items = grouped[month]
        temporal.append({
            "month":                      month,
            "installation_reussie":       round(sum(_as_binary(r.installation_reussie) for r in items) / len(items), 3),
            "client_satisfait":           round(sum(_as_binary(r.client_satisfait) for r in items) / len(items), 3),
            "client_a_reclame":           round(sum(_as_binary(r.client_a_reclame) for r in items) / len(items), 3),
            "Duree_installation_minutes": round(float(np.mean([r.duree_installation_minutes for r in items])), 1),
            "nombre_essais_installation": round(float(np.mean([r.nombre_essais_installation for r in items])), 2),
            "nombre_reclamations_client": round(float(np.mean([r.nombre_reclamations_client for r in items])), 2),
        })
    return temporal[-24:]


# ════════════════════════════════════════════════════════════════════════════
# ALERTS HELPER
# ════════════════════════════════════════════════════════════════════════════

def _build_alerts(
    taux_reussite: float,
    taux_risque: float,
    taux_reclamation: float,
    avg_duration: float,
) -> list[dict]:
    alerts = []
    if taux_reussite < 70:
        alerts.append({"type": "warning", "message": f"⚠️ Baisse du taux de réussite : {taux_reussite}%"})
    if taux_risque > 30:
        alerts.append({"type": "danger",  "message": f"🔴 Hausse clients à risque : {taux_risque}%"})
    if taux_reclamation > 25:
        alerts.append({"type": "warning", "message": f"⚠️ Hausse réclamations : {taux_reclamation}%"})
    if avg_duration > 90:
        alerts.append({"type": "info",    "message": "ℹ️ Dérive temporelle anormale sur la durée d'installation"})
    return alerts


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — VUE GLOBALE
# API utilisée par: frontend/app/(dashboard)/directeur/page.tsx
# Objectif: KPIs synthétiques, alertes, et figures globales du tableau de bord.
# ════════════════════════════════════════════════════════════════════════════

def dashboard_kpis(db: Session) -> dict:
    rows = _rows(db)
    total = len(rows)
    if total == 0:
        return {
            "nb_installations": 0, "taux_reussite": 0, "taux_satisfaction": 0,
            "taux_reclamation": 0, "duree_moyenne": 0, "nb_moyen_essais": 0,
            "taux_clients_risque": 0, "kpi_problemes": {}, "alerts": [], "plotly_figures": {},
        }

    success = sum(_as_binary(r.installation_reussie) for r in rows)
    sat     = sum(_as_binary(r.client_satisfait)     for r in rows)
    claim   = sum(_as_binary(r.client_a_reclame)     for r in rows)
    risk    = sum(_client_risque(r) for r in rows)

    avg_duration = float(np.mean([r.duree_installation_minutes for r in rows]))
    avg_attempts = float(np.mean([r.nombre_essais_installation for r in rows]))

    taux_reussite    = round(success / total * 100, 1)
    taux_satisfaction= round(sat     / total * 100, 1)
    taux_reclamation = round(claim   / total * 100, 1)
    taux_risque      = round(risk    / total * 100, 1)

    all_flags = [_remarques_flags(r.remarques) for r in rows]
    kpi_problemes = {
        key: round(sum(f[key] for f in all_flags) / total, 3)
        for key in ["pb_reseau", "pb_configuration", "pb_materiel", "pb_version", "pb_aucun"]
    }

    alerts = _build_alerts(taux_reussite, taux_risque, taux_reclamation, avg_duration)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Réussite", "Satisfaction", "Réclamation", "Risque"],
        y=[taux_reussite, taux_satisfaction, taux_reclamation, taux_risque],
        marker_color=["#2ecc71", "#3498db", "#e74c3c", "#e67e22"],
    ))
    fig.update_layout(template="plotly_white", title="KPI globaux (%)")

    fig_pb = go.Figure()
    fig_pb.add_trace(go.Bar(
        x=list(kpi_problemes.keys()),
        y=list(kpi_problemes.values()),
        marker_color="#6d6fd6",
    ))
    fig_pb.update_layout(template="plotly_white", title="Fréquence des types de problèmes")

    response = {
        "nb_installations":   total,
        "taux_reussite":      taux_reussite,
        "taux_satisfaction":  taux_satisfaction,
        "taux_reclamation":   taux_reclamation,
        "duree_moyenne":      round(avg_duration, 1),
        "nb_moyen_essais":    round(avg_attempts, 2),
        "taux_clients_risque": taux_risque,
        "kpi_problemes":      kpi_problemes,
        "alerts":             alerts,
        "plotly_figures":     {"kpis": _figure_json(fig), "problemes": _figure_json(fig_pb)},
    }
    return _to_serializable(response)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYSE PAR VARIABLE
# API utilisée par: frontend/app/(dashboard)/directeur/analysis/page.tsx
# Objectif: construire l'analyse détaillée par variable cible.
# ════════════════════════════════════════════════════════════════════════════

def target_analysis(db: Session, variable: str) -> dict:
    global _ANALYSIS_CACHE
    now = datetime.now()
    signature = _analysis_signature(db)
    cache_key = (variable, _ANALYSIS_CACHE_VERSION, signature)

    cached = _ANALYSIS_CACHE.get(cache_key)
    if cached is not None:
        elapsed = (now - cached["timestamp"]).total_seconds()
        if elapsed < _ANALYSIS_CACHE_TTL_SECONDS:
            return cached["result"]

    result = _target_analysis_impl(db, variable)
    _ANALYSIS_CACHE[cache_key] = {"result": result, "timestamp": now}
    return result


def _target_analysis_impl(db: Session, variable: str) -> dict:
    start = time.perf_counter()
    rows = _rows(db)
    df = None
    bundle: dict = {}
    temporal = _kpi_temporel(rows)

    def _temporal_value(item: dict) -> float:
        return float(item.get(variable, item.get(variable.replace("_encoded", ""), 0)))

    def _count_groups(label_fn) -> list[dict]:
        grouped: dict[str, int] = defaultdict(int)
        for row in rows:
            grouped[label_fn(row)] += 1
        return sorted(
            [{"label": label, "value": count} for label, count in grouped.items()],
            key=lambda item: item["value"],
            reverse=True,
        )

    target_col = variable

    if variable == "installation_reussie":
        target_col = "installation_reussie_encoded"

    elif variable == "client_satisfait":
        target_col = "client_satisfait_encoded"

    elif variable == "client_a_reclame":
        target_col = "client_a_reclame_encoded"

    if not df_agg.empty and target_col in df_agg.columns:
        prod_df = df_agg.groupby("Nom_produit")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            prod_df[target_col] = (prod_df[target_col] * 100).round(2)
        by_product = [{"product": r["Nom_produit"], "value": r[target_col]} for _, r in prod_df.iterrows()]

        zone_df = df_agg.groupby("Zone_urbanisation")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            zone_df[target_col] = (zone_df[target_col] * 100).round(2)
        by_zone_urbanisation = [{"zone": r["Zone_urbanisation"], "value": r[target_col]} for _, r in zone_df.iterrows()]

        os_df = df_agg.groupby("Systeme_exploitation_poste")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            os_df[target_col] = (os_df[target_col] * 100).round(2)
        by_systeme_exploitation_poste = [{"systeme_exploitation_poste": r["Systeme_exploitation_poste"], "value": r[target_col]} for _, r in os_df.iterrows()]

        ver_df = df_agg.groupby("version_produit")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            ver_df[target_col] = (ver_df[target_col] * 100).round(2)
        by_version_produit = [{"version_produit": r["version_produit"], "value": r[target_col]} for _, r in ver_df.iterrows()]

        taille_df = df_agg.groupby(df_agg["Taille_site_postes"].apply(lambda v: _cat_taille(float(v) if v is not None else 0)))[target_col].mean().reset_index()
        taille_df.columns = ["taille_site", target_col]
        if target_col.endswith("_encoded"):
            taille_df[target_col] = (taille_df[target_col] * 100).round(2)
        by_taille_site_postes = [{"taille_site": r["taille_site"], "value": r[target_col]} for _, r in taille_df.iterrows()]

        type_df = df_agg.groupby("Type_client")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            type_df[target_col] = (type_df[target_col] * 100).round(2)
        by_type_client = [{"type_client": r["Type_client"], "value": r[target_col]} for _, r in type_df.iterrows()]

        probl_df = df_agg.groupby("Remarques")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            probl_df[target_col] = (probl_df[target_col] * 100).round(2)
        by_type_probleme = [{"type_probleme": r["Remarques"], "value": r[target_col]} for _, r in probl_df.iterrows()]

        cat_df = df_agg.groupby("cat_debit")[target_col].mean().reset_index()
        if target_col.endswith("_encoded"):
            cat_df[target_col] = (cat_df[target_col] * 100).round(2)
        by_cat_debit_o = [{"cat_debit": r["cat_debit"], "value": r[target_col]} for _, r in cat_df.iterrows()]

    else:
        by_product = [
            {"product": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: row.nom_produit or "Inconnu")
        ]
        by_zone_urbanisation = [
            {"zone": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: _zone_urbanisation(row.gouvernorat))
        ]
        by_systeme_exploitation_poste = [
            {"systeme_exploitation_poste": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: row.systeme_exploitation_poste)
        ]
        by_version_produit = [
            {"version_produit": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: str(row.version_produit) if row.version_produit is not None else "Inconnue")
        ]
        by_taille_site_postes = [
            {"taille_site": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: _cat_taille(float(row.taille_site_postes)))
        ]
        by_type_client = [
            {"type_client": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: row.type_client or "Inconnu")
        ]
        by_type_probleme = [
            {"type_probleme": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: row.remarques or "Non renseigné")
        ]
        by_cat_debit_o = [
            {"cat_debit": item["label"], "value": item["value"]}
            for item in _count_groups(lambda row: _cat_debit(float(row.debit_reseau_mbps)))
        ]

    records = []
    for r in rows:
        try:
            debit = float(r.debit_reseau_mbps) if r.debit_reseau_mbps is not None else 0.0
        except Exception:
            debit = 0.0
        records.append({
            "Systeme_exploitation_poste": r.systeme_exploitation_poste,
            "installation_reussie_encoded": _as_binary(r.installation_reussie),
            "Zone_urbanisation": _zone_urbanisation(r.gouvernorat),
            "version_produit": str(r.version_produit),
            "Remarques": (r.remarques or "")[:100],
            "Type_client": r.type_client,
            "Taille_site_postes": r.taille_site_postes,
            "Nom_produit": r.nom_produit,
            "cat_debit": _cat_debit(debit),
            "client_satisfait_encoded": _as_binary(r.client_satisfait),
            "client_a_reclame_encoded": _as_binary(getattr(r, "client_a_reclame", False)),
            "client_risque": _client_risque(r),
            "Duree_installation_minutes": getattr(r, "duree_installation_minutes", None),
            "nombre_essais_installation": getattr(r, "nombre_essais_installation", None),
            "nombre_reclamations_client": getattr(r, "nombre_reclamations_client", None),
        })
    df_agg = pd.DataFrame(records) 

    target_col = variable

    if variable == "installation_reussie":
        target_col = "installation_reussie_encoded"

    elif variable == "client_satisfait":
        target_col = "client_satisfait_encoded"

    elif variable == "client_a_reclame":
        target_col = "client_a_reclame_encoded"

    # ════════════════════════════════════════════════════════════════════════════
    # KPI OPÉRATIONNELS + VISUALISATIONS
    # ════════════════════════════════════════════════════════════════════════════

    if not df_agg.empty and target_col in df_agg.columns:
        os_perf = (
            df_agg.groupby("Systeme_exploitation_poste")[target_col]
            .mean()
            .reset_index()
        )
        # normalize to percentage when it's an encoded rate
        if target_col.endswith("_encoded"):
            os_perf[target_col] = (os_perf[target_col] * 100).round(2)
    else:
        # fallback: counts by OS
        if not df_agg.empty:
            os_perf = (
                df_agg["Systeme_exploitation_poste"].value_counts().reset_index()
            )
            os_perf.columns = ["Systeme_exploitation_poste", "installation_reussie_encoded"]
        else:
            os_perf = pd.DataFrame(
                columns=["Systeme_exploitation_poste", "installation_reussie_encoded"]
            )

    # ---------- KPI VERSION ----------
    if not df_agg.empty and target_col in df_agg.columns:
        # show mean of the target per version (rate or numeric)
        kpi_version = (
            df_agg.groupby("version_produit")[target_col]
            .mean()
            .reset_index()
        )
        if target_col.endswith("_Encoded") or target_col.endswith("_encoded"):
            kpi_version[target_col] = (kpi_version[target_col] * 100).round(2)
    elif not df_agg.empty:
        # fallback: counts per version
        kpi_version = (
            df_agg["version_produit"].value_counts().reset_index()
        )
        kpi_version.columns = ["version_produit", "count"]
    else:
        kpi_version = pd.DataFrame(
            columns=["version_produit", "count"]
        )

    # ---------- KPI CLIENT (target-aware) ----------
    if not df_agg.empty and target_col in df_agg.columns:

        client_target = (
            df_agg.groupby("Type_client")[target_col]
            .mean()
            .reset_index()
        )

        if target_col.endswith("_encoded"):
            client_target[target_col] = (client_target[target_col] * 100).round(2)

    elif not df_agg.empty:

        client_target = (
            df_agg["Type_client"]
            .value_counts()
            .reset_index()
        )

        client_target.columns = ["Type_client", "count"]

    else:
        client_target = pd.DataFrame(columns=["Type_client", "count"])

    # ---------- KPI CATÉGORIE DÉBIT ----------
    if not df_agg.empty and target_col in df_agg.columns:
        kpi_cat = (
            df_agg.groupby("cat_debit")[target_col]
            .mean()
            .reset_index()
        )
        if target_col.endswith("_encoded"):
            kpi_cat[target_col] = (kpi_cat[target_col] * 100).round(2)
    else:
        # fallback to previous multi-metric view
        if not df_agg.empty:
            kpi_cat = (
                df_agg.groupby("cat_debit")
                .agg({
                    "installation_reussie_encoded": "mean",
                    "client_satisfait_encoded": "mean",
                    "client_risque": "mean",
                })
                .reset_index()
            )
            for col in [
                "installation_reussie_encoded",
                "client_satisfait_encoded",
                "client_risque",
            ]:
                kpi_cat[col] = (kpi_cat[col] * 100).round(2)
        else:
            kpi_cat = pd.DataFrame(
                columns=[
                    "cat_debit",
                    "installation_reussie_encoded",
                    "client_satisfait_encoded",
                    "client_risque",
                ]
            )

    # ════════════════════════════════════════════════════════════════════════════
    # FIGURES PLOTLY
    # ════════════════════════════════════════════════════════════════════════════

    # ---------- BAR : Remarques / KPI par version
    if not kpi_version.empty and target_col in kpi_version.columns:
        y_col = target_col
        title = f"{variable} par version produit"
        color_col = target_col
    elif not kpi_version.empty and "count" in kpi_version.columns:
        y_col = "count"
        title = "Remarques par version produit"
        color_col = "count"
    else:
        y_col = None
        title = "Remarques par version produit"
        color_col = None

    if y_col is not None:
        fig_kpi_version = px.bar(
            kpi_version,
            x="version_produit",
            y=y_col,
            color=color_col,
            color_continuous_scale="Viridis",
            title=title,
        )
        fig_kpi_version.update_layout(template="plotly_white")
    else:
        fig_kpi_version = go.Figure()

    # ---------- BAR : Performance OS ----------
    # OS performance: show selected target if available
    if not os_perf.empty and target_col in os_perf.columns:
        fig_os_perf = px.bar(
            os_perf,
            x="Systeme_exploitation_poste",
            y=target_col,
            color=target_col,
            color_continuous_scale="Plasma",
            title=f"{variable} par système d'exploitation",
        )
        fig_os_perf.update_layout(template="plotly_white", yaxis_title=("Taux (%)" if target_col.endswith("_encoded") else None))
    else:
        fig_os_perf = px.bar(
            os_perf,
            x="Systeme_exploitation_poste",
            y=os_perf.columns[1] if os_perf.shape[1] > 1 else os_perf.columns[0],
            color=os_perf.columns[1] if os_perf.shape[1] > 1 else os_perf.columns[0],
            color_continuous_scale="Plasma",
            title="Performance par système d'exploitation",
        )
        fig_os_perf.update_layout(template="plotly_white")

    # ---------- BOX : variable cible par type client ----------
    if not df_agg.empty and "Type_client" in df_agg.columns:

        df_filtered = df_agg[df_agg[target_col].notnull()].copy()

        fig_client_box = px.box(
            df_filtered,
            x="Type_client",
            y="Taille_site_postes",
            color="Type_client",
            title=f"Taille site poste par type client ({target_col})",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig_client_box.update_layout(
            template="plotly_white",
            yaxis_title="Taille site poste"
        )
    
    else:

        fig_client_box = px.box(
            df_agg,
            x="Type_client",
            y="Taille_site_postes",
            color="Type_client",
            title="Taille des sites par type client",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

    # ---------- PIE : Distribution type client (target-aware) ----------
    if target_col in client_target.columns:

        fig_client_pie = px.pie(
            client_target,
            names="Type_client",
            values=target_col,
            title=f"{variable} par type client",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )

    else:

        fig_client_pie = px.pie(
            client_target,
            names="Type_client",
            values="count",
            title="Distribution des installations par type client",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )

    fig_client_pie.update_traces(textinfo="percent+label")

    # product distribution handled below in a target-aware manner

    # ---------- BAR : KPI débit ----------
    # kpi by debit: show selected target if available
    if not kpi_cat.empty and target_col in kpi_cat.columns:
        fig_kpi_cat = px.bar(
            kpi_cat,
            x="cat_debit",
            y=target_col,
            color=target_col,
            color_continuous_scale="Plasma",
            title=f"{variable} par catégorie de débit",
        )
        fig_kpi_cat.update_layout(template="plotly_white", yaxis_title=("Taux (%)" if target_col.endswith("_encoded") else None))
    else:
        fig_kpi_cat = px.bar(
            kpi_cat,
            x="cat_debit",
            y=[
                "installation_reussie_encoded",
                "client_satisfait_encoded",
                "client_risque",
            ],
            barmode="group",
            title="Impact du débit réseau",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_kpi_cat.update_layout(template="plotly_white", yaxis_title="Taux (%)")

    # ════════════════════════════════════════════════════════════════════════════
    # FIGURE TEMPORELLE
    # ════════════════════════════════════════════════════════════════════════════

    fig_t = go.Figure()

    fig_t.add_trace(
        go.Scatter(
            x=[p["month"] for p in temporal],
            y=[_temporal_value(p) for p in temporal],
            mode="lines+markers",
            name=variable,
            line=dict(color="#4F46E5", width=3),
        )
    )

    fig_t.update_layout(
        template="plotly_white",
        title=f"Évolution de {variable}",
    )

    # ════════════════════════════════════════════════════════════════════════════
    # PRODUCT: intelligent KPI or counts depending on target
    # ════════════════════════════════════════════════════════════════════════════
    if not df_agg.empty and target_col in df_agg.columns:

        prod_by_product = (
            df_agg.groupby("Nom_produit")[target_col]
            .mean()
            .reset_index()
        )

        prod_by_product[target_col] = (
            prod_by_product[target_col] * 100
        ).round(2)

        fig_p = px.pie(
            prod_by_product,
            names="Nom_produit",
            values=target_col,
            title=f"{variable} par produit CNI",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig_p.update_traces(
            textinfo="percent+label"
        )

        fig_p.update_layout(
            template="plotly_white"
        )

    else:

        if not df_agg.empty:

            prod_by_product = (
                df_agg["Nom_produit"]
                .value_counts()
                .reset_index()
            )

            prod_by_product.columns = [
                "Nom_produit",
                "value",
            ]

        else:

            prod_by_product = pd.DataFrame(
                columns=["Nom_produit", "value"]
            )

        fig_p = px.pie(
            prod_by_product,
            names="Nom_produit",
            values="value",
            title="Distribution par produit CNI",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig_p.update_traces(
            textinfo="percent+label"
        )

        fig_p.update_layout(
            template="plotly_white"
        )

    # ════════════════════════════════════════════════════════════════════════════
    # PIE : ZONE URBANISATION
    # ════════════════════════════════════════════════════════════════════════════

    # ZONE URBANISATION — target-aware horizontal bar
    if not df_agg.empty and target_col in df_agg.columns:

        zone_by_area = (
            df_agg.groupby("Zone_urbanisation")[target_col]
            .count()
            .reset_index()
        )

        if target_col.endswith("_encoded"):
            zone_by_area[target_col] = (zone_by_area[target_col] * 100).round(2)

        fig_zone = px.bar(
            zone_by_area,
            x=target_col,
            y="Zone_urbanisation",
            orientation="h",
            color=target_col,
            color_continuous_scale="Viridis",
            title=f"{variable} par zone d'urbanisation",
        )

        fig_zone.update_layout(
            template="plotly_white",
            yaxis_title="Zone",
            xaxis_title=("Taux (%)" if target_col.endswith("_encoded") else "Nombre"),
        )


    # ════════════════════════════════════════════════════════════════════════════
    # HISTOGRAM: Problem counts by type
    # ════════════════════════════════════════════════════════════════════════════
    
    # Count occurrences of each problem type flag
    problem_flags = ["pb_reseau", "pb_configuration", "pb_materiel", "pb_version", "pb_aucun"]
    problem_counts = {}
    for flag in problem_flags:
        if flag in df_agg.columns:
            problem_counts[flag.replace("pb_", "").capitalize()] = int(df_agg[flag].sum())
    
    fig_problems = go.Figure()
    
    if problem_counts:
        fig_problems.add_trace(go.Bar(
            x=list(problem_counts.keys()),
            y=list(problem_counts.values()),
            marker_color="#e74c3c",
        ))
    else:
        # Si pas de données, afficher un graphique vide avec message
        fig_problems.add_trace(go.Bar(
            x=["Pas de données"],
            y=[0],
            marker_color="#e74c3c",
        ))
    
    fig_problems.update_layout(
        template="plotly_white",
        title=f"Distribution des problèmes détectés — {variable}",
        xaxis_title="Type de problème",
        yaxis_title="Nombre d'occurrences",
    )

    # ════════════════════════════════════════════════════════════════════════════
    # RETURN
    # ════════════════════════════════════════════════════════════════════════════

    response = {
        "variable": variable,

        "temporal": [
            {
                **item,
                "value": _temporal_value(item),
            }
            for item in temporal
        ],

        "by_product": by_product,

        "by_zone_urbanisation": by_zone_urbanisation,

        "by_systeme_exploitation_poste":
            by_systeme_exploitation_poste,

        "by_version_produit":
            by_version_produit,

        "by_taille_site_postes":
            by_taille_site_postes,

        "by_type_client":
            by_type_client,


        "by_type_probleme":
            by_type_probleme,

        "by_cat_debit_o":
            by_cat_debit_o,

        "plotly_figures": {

            "temporal": _figure_json(fig_t),

            "by_product": _figure_json(fig_p),

            "by_zone_urbanisation": _figure_json(fig_zone),

            "kpi_version": _figure_json(fig_kpi_version),

            "os_performance": _figure_json(fig_os_perf),

            "client_box": _figure_json(fig_client_box),

            "client_pie": _figure_json(fig_client_pie),

            "kpi_cat_debit": _figure_json(fig_kpi_cat),

            "problems_histogram": _figure_json(fig_problems),
        },

        "_timings": {
            "total_ms": round(
                (time.perf_counter() - start) * 1000,
                2
            ),
            "n_rows": len(rows),
        },
    }
    
    return _to_serializable(response)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PREVISIONS
# API utilisée par: frontend/app/(dashboard)/directeur/predictions/page.tsx
# Objectif: prévisions mensuelles SARIMA.
# ════════════════════════════════════════════════════════════════════════════

import os
import pickle
from typing import Any, Dict, List
from datetime import timedelta

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy.orm import Session
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from itertools import product
import numpy as np
_SARIMA_ORDERS_CACHE: dict | None = None
_SARIMA_ORDERS_CACHE_SIZE: int = 0
_SARIMA_ORDERS_LOCK = Lock()


def _build_weekly_series(rows: list) -> tuple[pd.DataFrame, list[str]]:
    targets = [
        "installation_reussie_encoded",
        "client_satisfait_encoded",
        "client_a_reclame_encoded",
        "Duree_installation_minutes",
    ]

    df = pd.DataFrame([{
        "date_installation":             pd.to_datetime(r.date_installation),
        "installation_reussie_encoded":  float(_as_binary(r.installation_reussie)),
        "client_satisfait_encoded":      float(_as_binary(r.client_satisfait)),
        "client_a_reclame_encoded":      float(_as_binary(r.client_a_reclame)),
        "Duree_installation_minutes":    float(r.duree_installation_minutes or 0),
    } for r in rows])

    df_weekly = (
        df.set_index("date_installation")[targets]
        .resample("W")
        .mean()
        .rolling(3)
        .mean()
        .dropna()
    )

    return df_weekly, targets


def _fit_sarima_orders(db: Session) -> dict:
    global _SARIMA_ORDERS_CACHE, _SARIMA_ORDERS_CACHE_SIZE

    rows = sorted(_rows(db), key=lambda r: r.date_installation)
    n_rows = len(rows)

    with _SARIMA_ORDERS_LOCK:
        if _SARIMA_ORDERS_CACHE is not None and n_rows == _SARIMA_ORDERS_CACHE_SIZE:
            return _SARIMA_ORDERS_CACHE

        df_weekly, targets = _build_weekly_series(rows)

        split_ratio = 0.8
        orders: dict = {}

        for var in targets:
            ts_var = df_weekly[var].dropna().astype(float)

            # notebook: split_idx = max(5, min(int(len*0.8), len-1))
            split_idx = int(len(ts_var) * split_ratio)
            split_idx = max(5, min(split_idx, len(ts_var) - 1))
            train = ts_var.iloc[:split_idx]

            print(f"[SARIMA] Grid search on train for {var} (n={len(train)})…")

            try:
                best_aic = np.inf
                best_order = (1, 0, 0)
                best_seasonal = (0, 0, 0, 4)
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ConvergenceWarning)
                    
                    # Grid search over ARIMA/SARIMA parameters
                    for p, d, q in product([0, 1, 2], [0, 1], [0, 1, 2]):
                        for P, D, Q in product([0, 1], [0, 1], [0, 1]):
                            try:
                                model = SARIMAX(
                                    train,
                                    order=(p, d, q),
                                    seasonal_order=(P, D, Q, 4),
                                    enforce_stationarity=False,
                                    enforce_invertibility=False
                                )
                                result = model.fit(disp=False, maxiter=200)
                                if result.aic < best_aic:
                                    best_aic = result.aic
                                    best_order = (p, d, q)
                                    best_seasonal = (P, D, Q, 4)
                            except Exception:
                                pass
            except Exception as e:
                print(f"[SARIMA] Grid search failed for {var}: {e} — using fallback (1,0,0)")
                best_order    = (1, 0, 0)
                best_seasonal = (0, 0, 0, 4)

            orders[var] = {"order": best_order, "seasonal_order": best_seasonal}
            print(f"[SARIMA] {var}: order={best_order}, seasonal={best_seasonal}")

        _SARIMA_ORDERS_CACHE      = orders
        _SARIMA_ORDERS_CACHE_SIZE = n_rows
        return orders


def predictions(db: Session, forecast_weeks: int = 30) -> dict:
    rows = sorted(_rows(db), key=lambda r: r.date_installation)

    if not rows:
        return {"predictions": [], "evaluation": {}, "plotly_figures": {}}

    df_weekly, targets = _build_weekly_series(rows)

    if df_weekly.empty:
        return {"predictions": [], "evaluation": {}, "plotly_figures": {}}

    orders = _fit_sarima_orders(db)

    split_ratio  = 0.8
    last_date    = df_weekly.index[-1]

    future_preds: List[dict] = []
    plotly_figs:  dict       = {}

    for var in targets:
        try:
            ts_var = df_weekly[var].dropna().astype(float)

            split_idx = int(len(ts_var) * split_ratio)
            split_idx = max(5, min(split_idx, len(ts_var) - 1))
            train = ts_var.iloc[:split_idx]
            test  = ts_var.iloc[split_idx:]

            best_order    = orders[var]["order"]
            best_seasonal = orders[var]["seasonal_order"]

            rolling_preds: list[float] = []
            if len(test) > 0:
                history = list(train.astype(float).tolist())
                for idx, t_idx in enumerate(test.index):
                    try:
                        model_tf = SARIMAX(
                            history,
                            order=best_order,
                            seasonal_order=best_seasonal,
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                        )
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", ConvergenceWarning)
                            fit_tf = model_tf.fit(disp=False, maxiter=200)
                        pred = float(np.asarray(fit_tf.forecast(steps=1)).ravel()[0])
                    except Exception:
                        pred = float(np.mean(history[-4:])) if len(history) > 0 else 0.0
                    rolling_preds.append(pred)
                    try:
                        history.append(float(test.iloc[idx]))
                    except Exception:
                        history.append(pred)

            pred_series = pd.Series(rolling_preds, index=test.index, name=var)

            future_vals: list[float] = []
            future_lower: list[float] = []
            future_upper: list[float] = []
            try:
                fut_model = SARIMAX(
                    ts_var,
                    order=best_order,
                    seasonal_order=best_seasonal,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ConvergenceWarning)
                    fut_fit = fut_model.fit(disp=False, maxiter=200)
                forecast_res = fut_fit.get_forecast(steps=forecast_weeks)
                future_vals = np.asarray(forecast_res.predicted_mean).ravel().astype(float).tolist()
                conf = forecast_res.conf_int(alpha=0.05)
                conf_vals = np.asarray(conf)
                future_lower = conf_vals[:, 0].astype(float).tolist()
                future_upper = conf_vals[:, 1].astype(float).tolist()
            except Exception:
                fallback = float(np.mean(ts_var.iloc[-4:])) if len(ts_var) > 0 else 0.0
                future_vals = [fallback] * forecast_weeks
                future_lower = [fallback] * forecast_weeks
                future_upper = [fallback] * forecast_weeks

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=train.index.astype(str).tolist(),
                y=train.tolist(),
                mode="lines",
                name="Train",
                line=dict(color="#4F46E5", width=2),
            ))

            if len(test) > 0:
                fig.add_trace(go.Scatter(
                    x=test.index.astype(str).tolist(),
                    y=test.tolist(),
                    mode="lines",
                    name="Test (réel)",
                    line=dict(color="#10B981", width=2),
                ))
                fig.add_trace(go.Scatter(
                    x=pred_series.index.astype(str).tolist(),
                    y=pred_series.tolist(),
                    mode="lines",
                    name="Prédiction (test)",
                    line=dict(color="#F59E0B", width=2, dash="dash"),
                ))

            future_dates = [
                str((last_date + timedelta(weeks=i + 1)).date())
                for i in range(forecast_weeks)
            ]
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=future_upper,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=future_lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(239,68,68,0.15)",
                name="IC 95%",
                hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=future_vals,
                mode="lines+markers",
                name="Prévision future",
                line=dict(color="#EF4444", width=2, dash="dot"),
                marker=dict(size=4),
            ))

            fig.update_layout(
                template="plotly_white",
                title=f"SARIMA — {var}",
                xaxis=dict(title="Semaine", title_standoff=24),
                yaxis_title="Valeur",
                legend=dict(orientation="h", yanchor="top", y=-0.32, xanchor="left", x=0),
                margin=dict(t=70, b=130, l=50, r=20),
            )

            plotly_figs[f"sarima_{var}"] = fig.to_dict()

            # Also expose a "future-only" figure for the dashboard visualization
            try:
                fig_future = go.Figure()
                fig_future.add_trace(go.Scatter(
                    x=future_dates,
                    y=future_vals,
                    mode="lines+markers",
                    name="Prévision future",
                    line=dict(color="#EF4444", width=2, dash="dot"),
                    marker=dict(size=4),
                ))
                fig_future.update_layout(template="plotly_white", title=f"Prévision future — {var}", xaxis=dict(title="Semaine"), yaxis_title="Valeur", margin=dict(t=40, b=60))
                plotly_figs[f"sarima_{var}_future"] = fig_future.to_dict()
            except Exception:
                pass

            # --- ARIMA variant (optional: uses pmdarima.auto_arima when available) ---
            try:
                # select order using auto_arima on the train set if available
                ar_order = None
                if auto_arima is not None and len(train) >= 6:
                    try:
                        aa = auto_arima(train, seasonal=False, error_action="ignore", suppress_warnings=True, maxiter=50)
                        ar_order = tuple(aa.order)
                    except Exception:
                        ar_order = None

                if ar_order is None:
                    ar_order = (1, 0, 0)

                # rolling predictions on test (not stored in response, but could be)
                if len(test) > 0:
                    history = list(train.astype(float).tolist())
                    ar_rolling_preds = []
                    for idx in range(len(test)):
                        try:
                            mdl = ARIMA(history, order=ar_order)
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", ConvergenceWarning)
                                fitted = mdl.fit()
                            pred = float(np.asarray(fitted.forecast(steps=1)).ravel()[0])
                        except Exception:
                            pred = float(np.mean(history[-4:])) if len(history) > 0 else 0.0
                        ar_rolling_preds.append(pred)
                        try:
                            history.append(float(test.iloc[idx]))
                        except Exception:
                            history.append(pred)

                # forecast future on the whole series
                try:
                    mdl_full = ARIMA(ts_var, order=ar_order)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", ConvergenceWarning)
                        fit_full = mdl_full.fit()
                    ar_fore = fit_full.get_forecast(steps=forecast_weeks)
                    ar_vals = np.asarray(ar_fore.predicted_mean).ravel().astype(float).tolist()
                    ar_conf = np.asarray(ar_fore.conf_int(alpha=0.05))
                    ar_low = ar_conf[:, 0].astype(float).tolist()
                    ar_up = ar_conf[:, 1].astype(float).tolist()
                except Exception:
                    ar_vals = [float(np.mean(ts_var.iloc[-4:])) if len(ts_var) > 0 else 0.0] * forecast_weeks
                    ar_low = ar_vals.copy()
                    ar_up = ar_vals.copy()

                # build ARIMA future-only figure
                try:
                    fig_ar = go.Figure()
                    fig_ar.add_trace(go.Scatter(
                        x=future_dates,
                        y=ar_vals,
                        mode="lines+markers",
                        name="Prévision ARIMA",
                        line=dict(color="#2563EB", width=2),
                        marker=dict(size=4),
                    ))
                    fig_ar.update_layout(template="plotly_white", title=f"ARIMA — Prévision future — {var}", xaxis=dict(title="Semaine"), yaxis_title="Valeur", margin=dict(t=40, b=60))
                    plotly_figs[f"arima_{var}"] = fig_ar.to_dict()
                    plotly_figs[f"arima_{var}_future"] = fig_ar.to_dict()
                except Exception:
                    pass
            except Exception:
                # don't fail the whole predictions endpoint on ARIMA issues
                pass

            for i, (date_str, val) in enumerate(zip(future_dates, future_vals)):
                if len(future_preds) <= i:
                    future_preds.append({"date": date_str})
                if var != "Duree_installation_minutes":
                    future_preds[i][var] = round(max(0.0, min(1.0, val)), 3)
                    if i < len(future_lower) and i < len(future_upper):
                        future_preds[i][f"{var}_lower"] = round(max(0.0, min(1.0, future_lower[i])), 3)
                        future_preds[i][f"{var}_upper"] = round(max(0.0, min(1.0, future_upper[i])), 3)
                else:
                    future_preds[i][var] = round(max(0.0, val), 1)
                    if i < len(future_lower) and i < len(future_upper):
                        future_preds[i][f"{var}_lower"] = round(max(0.0, future_lower[i]), 1)
                        future_preds[i][f"{var}_upper"] = round(max(0.0, future_upper[i]), 1)

        except Exception as e:
            print(f"[SARIMA] Error for {var}: {e}")

    return _to_serializable({
        "predictions":     future_preds,
        "plotly_figures":  plotly_figs,
    })


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ML_PREDICTION
# API utilisée par: frontend/app/(dashboard)/directeur/predictions/page.tsx
# Objectif: fournir la liste des modèles et une prédiction simple par cible.
# ════════════════════════════════════════════════════════════════════════════

MODEL_SPECS: dict[str, dict[str, Any]] = {
    "client_risque": {
        "display_name": "Risque Client",
        "description": "Estime si le client présente un risque élevé avant l'installation.",
        "model_type": "classification",
        "input_fields": ["type_client", "systeme_exploitation_poste", "debit_reseau_mbps", "taille_site_postes", "nombre_essais_installation", "nombre_reclamations_client", "gouvernorat"],
    },
    "installation_reussie_encoded": {
        "display_name": "Succès Installation",
        "description": "Prédit la probabilité que l'installation aboutisse avec succès.",
        "model_type": "classification",
        "input_fields": ["type_client", "systeme_exploitation_poste", "debit_reseau_mbps", "taille_site_postes", "nombre_essais_installation", "nombre_reclamations_client"],
    },
    "client_satisfait_encoded": {
        "display_name": "Satisfaction Client",
        "description": "Prédit si le client sera satisfait après l'installation.",
        "model_type": "classification",
        "input_fields": ["type_client", "systeme_exploitation_poste", "debit_reseau_mbps", "taille_site_postes", "nombre_essais_installation", "nombre_reclamations_client"],
    },
    "client_a_reclame_encoded": {
        "display_name": "Réclamations Client",
        "description": "Prédit si le client risque de déposer une réclamation.",
        "model_type": "classification",
        "input_fields": ["type_client", "systeme_exploitation_poste", "debit_reseau_mbps", "taille_site_postes", "nombre_essais_installation", "nombre_reclamations_client"],
    },
    "Duree_installation_minutes": {
        "display_name": "Durée Installation",
        "description": "Estime le temps d'installation en minutes.",
        "model_type": "regression",
        "input_fields": ["type_client", "systeme_exploitation_poste", "debit_reseau_mbps", "taille_site_postes", "nombre_essais_installation", "nombre_reclamations_client", "mode_installation", "gouvernorat"],
    },
}

FIELD_LIBRARY: dict[str, dict[str, Any]] = {
    "type_client": {"name": "type_client", "label": "Type de client", "type": "select"},
    "systeme_exploitation_poste": {"name": "systeme_exploitation_poste", "label": "Système d'exploitation", "type": "select"},
    "debit_reseau_mbps": {"name": "debit_reseau_mbps", "label": "Débit réseau (Mbps)", "type": "number"},
    "taille_site_postes": {"name": "taille_site_postes", "label": "Taille du site (postes)", "type": "number"},
    "nombre_essais_installation": {"name": "nombre_essais_installation", "label": "Nombre d'essais", "type": "number"},
    "nombre_reclamations_client": {"name": "nombre_reclamations_client", "label": "Nombre de réclamations", "type": "number"},
    "mode_installation": {"name": "mode_installation", "label": "Mode d'installation", "type": "select"},
    "gouvernorat": {"name": "gouvernorat", "label": "Gouvernorat", "type": "select"},
}

_PREDICTION_BUNDLE_CACHE: dict[str, Any] | None = None
_PREDICTION_BUNDLE_SIZE: int = 0
_PREDICTION_BUNDLE_LOCK = Lock()


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


class _RuleBasedPredictionModel:
    def __init__(self, task: str):
        self.task = task

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        scores = []
        for _, row in X.iterrows():
            score = 0.5
            score += 0.08 if _safe_float(row.get("debit_reseau_mbps"), 0.0) < 5 else -0.03
            score += 0.07 if _safe_int(row.get("nombre_essais_installation"), 0) > 2 else -0.02
            score += 0.05 if _safe_int(row.get("nombre_reclamations_client"), 0) > 0 else 0.0
            score += 0.04 if _safe_int(row.get("taille_site_postes"), 0) > 20 else 0.0
            if _normalize_text(row.get("gouvernorat"), "") in GOUVERNORATS_RISQUE:
                score += 0.05
            if _normalize_text(row.get("systeme_exploitation_poste"), "").lower() in {"windowsxp", "win7", "win8"}:
                score += 0.04
            if self.task == "regression":
                scores.append(max(0.0, 60.0 + score * 80.0))
            else:
                scores.append(min(max(score, 0.0), 1.0))
        return np.asarray(scores, dtype=float)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        scores = self._score(X)
        if self.task == "regression":
            return scores
        return (scores >= 0.55).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.task == "regression":
            raise AttributeError("predict_proba not available for regression")
        scores = self._score(X)
        return np.column_stack([1.0 - scores, scores])


def _build_input_features(model_name: str, raw_features: dict[str, Any], df: pd.DataFrame | None = None) -> dict[str, Any]:
    return {
        "type_client": _normalize_text(raw_features.get("type_client"), "Inconnu"),
        "systeme_exploitation_poste": _normalize_text(raw_features.get("systeme_exploitation_poste"), "Inconnu"),
        "debit_reseau_mbps": _safe_float(raw_features.get("debit_reseau_mbps"), 0.0),
        "taille_site_postes": _safe_int(raw_features.get("taille_site_postes"), 0),
        "nombre_essais_installation": _safe_int(raw_features.get("nombre_essais_installation"), 0),
        "nombre_reclamations_client": _safe_int(raw_features.get("nombre_reclamations_client"), 0),
        "mode_installation": _normalize_text(raw_features.get("mode_installation"), "Inconnu"),
        "gouvernorat": _normalize_text(raw_features.get("gouvernorat"), "Inconnu"),
    }


def _load_prediction_bundle(db: Session) -> tuple[pd.DataFrame, dict[str, Any]]:
    global _PREDICTION_BUNDLE_CACHE, _PREDICTION_BUNDLE_SIZE

    rows = _rows(db)
    df = _build_dataframe(rows)

    with _PREDICTION_BUNDLE_LOCK:
        if _PREDICTION_BUNDLE_CACHE is not None and len(rows) == _PREDICTION_BUNDLE_SIZE:
            return df, _PREDICTION_BUNDLE_CACHE

        bundle = {}
        for model_name, spec in MODEL_SPECS.items():
            bundle[model_name] = {
                "model": _RuleBasedPredictionModel(task=spec["model_type"]),
                "model_name": model_name,
                "features": spec["input_fields"],
                "task": spec["model_type"],
                "display_name": spec["display_name"],
            }

        _PREDICTION_BUNDLE_CACHE = bundle
        _PREDICTION_BUNDLE_SIZE = len(rows)
        return df, bundle


def _get_field_options(db: Session, field_name: str) -> list[str]:
    rows = _rows(db)
    values = set()
    for row in rows:
        value = getattr(row, field_name, None)
        if value and str(value).strip():
            values.add(str(value).strip())
    return sorted(list(values))


def _get_example_values(db: Session, field_names: list[str]) -> dict[str, Any]:
    rows = _rows(db)
    if not rows:
        return {}
    
    # Use first row as example
    first_row = rows[0]
    example_values = {}
    for field_name in field_names:
        if field_name in FIELD_LIBRARY:
            field_type = FIELD_LIBRARY[field_name]["type"]
            value = getattr(first_row, field_name, None)
            
            if field_type == "number":
                example_values[field_name] = _safe_float(value, 0.0)
            elif field_type == "select":
                example_values[field_name] = _normalize_text(value, "")
            else:
                example_values[field_name] = _normalize_text(value, "")
    
    return example_values


def list_models(db: Session) -> list[dict[str, Any]]:
    result = []
    for model_name, spec in MODEL_SPECS.items():
        input_fields = []
        for field_name in spec["input_fields"]:
            if field_name in FIELD_LIBRARY:
                field = FIELD_LIBRARY[field_name].copy()
                # Add options for select fields
                if field["type"] == "select":
                    field["options"] = _get_field_options(db, field_name)
                    field["placeholder"] = f"Choisir un {field['label'].lower()}"
                input_fields.append(field)
        
        result.append({
            "model_name": model_name,
            "display_name": spec["display_name"],
            "description": spec["description"],
            "model_type": spec["model_type"],
            "input_fields": input_fields,
            "required_features": spec["input_fields"],
            "example_values": _get_example_values(db, spec["input_fields"]),
        })
    return result


def init_training_background() -> Thread:
    from app.db.session import SessionLocal

    def _worker() -> None:
        db = SessionLocal()
        try:
            _load_prediction_bundle(db)
        finally:
            db.close()

    thread = Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def predict(db: Session, model_name: str, features: dict[str, Any]) -> dict[str, Any]:
    if model_name not in MODEL_SPECS:
        raise ValueError(f"Modèle inconnu: {model_name}")

    _, bundle = _load_prediction_bundle(db)
    if model_name not in bundle:
        raise ValueError(f"Aucune version entraînée trouvée pour {model_name}")

    model_bundle = bundle[model_name]
    model = model_bundle["model"]
    feature_names = model_bundle["features"]

    feature_map = _build_input_features(model_name, features)
    row = {name: feature_map.get(name, 0) for name in feature_names}
    X = pd.DataFrame([row], columns=feature_names)

    raw_pred = model.predict(X)[0]
    is_classification = model_bundle["task"] == "classification"

    probability = None
    confidence = None
    prediction = float(raw_pred)
    if is_classification:
        prediction = int(raw_pred)
        proba = model.predict_proba(X)[0]
        probability = float(proba[1])
        confidence = float(max(proba))
        message = "Prédiction: OUI" if prediction == 1 else "Prédiction: NON"
    else:
        message = f"Durée estimée: {prediction:.1f} minutes"

    return {
        "model_name": model_name,
        "display_name": MODEL_SPECS[model_name]["display_name"],
        "model_type": model_bundle["task"],
        "prediction": prediction,
        "probability": probability,
        "confidence": confidence,
        "message": message,
        "model_backend": model_bundle["model_name"],
        "used_features": feature_names,
        "input_summary": features,
    }


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — RISQUE
# ════════════════════════════════════════════════════════════════════════════

def risk_analysis(db: Session) -> dict:
    _, model_cache = _get_models(db)
    rows  = _rows(db)
    total = len(rows)
    if total == 0:
        return {
            "taux_risque": 0, "nb_clients_risque": 0, "total_clients": 0,
            "score_distribution": [], "top_factors": [], "recommendations": [],
            "shap_importance": [], "plotly_figures": {},
        }

    scores     = [_score_risque(r) for r in rows]
    dist: dict[int, int] = defaultdict(int)
    for s in scores:
        dist[s] += 1

    at_risk = sum(1 for s in scores if s >= 3)

    factor_counts = {
        "Débit réseau faible":          sum(1 for r in rows if r.debit_reseau_mbps < 5),
        "Nombre d'essais élevé":        sum(1 for r in rows if r.nombre_essais_installation > 2),
        "Durée installation longue":    sum(1 for r in rows if r.duree_installation_minutes > 120),
        "OS ancien / instable":         sum(1 for r in rows if "windowsxp" in (r.systeme_exploitation_poste or "").lower()),
        "Produit GRB":                  sum(1 for r in rows if r.nom_produit == "GRB"),
        "Zone géographique difficile":  sum(1 for r in rows if r.gouvernorat in GOUVERNORATS_RISQUE),
        "Site de grande taille":        sum(1 for r in rows if r.taille_site_postes > 15),
    }

    top_factors = sorted(
        [{"factor": k, "count": v, "percentage": round(v / total * 100, 1)} for k, v in factor_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )

    shap_imp = []
    if model_cache is not None and "client_risque" in model_cache:
        try:
            b = model_cache["client_risque"]
            imp_df = _shap_importance(b["shap_values"], b["X_test"])
            shap_imp = [
                {"feature": row["feature"], "importance": round(row["importance"], 4)}
                for _, row in imp_df.head(10).iterrows()
            ]
        except Exception:
            shap_imp = []

    recommendations = [
        {"priority": 1, "action": "Améliorer le débit réseau",                     "impact": "Réduction des échecs d'installation",   "effort": "Moyen"},
        {"priority": 2, "action": "Mettre à jour la version du produit",           "impact": "Stabilité accrue",                       "effort": "Moyen"},
        {"priority": 3, "action": "Maintenance poste client (OS ancien)",          "impact": "Baisse du taux de réclamation",           "effort": "Élevé"},
        {"priority": 4, "action": "Éviter la télémaintenance sur zones difficiles","impact": "Meilleure réussite d'installation",       "effort": "Faible"},
        {"priority": 5, "action": "Planifier les installations hors weekend",      "impact": "Moins d'incidents",                      "effort": "Faible"},
    ]

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Bar(
        x=[str(k) for k in sorted(dist.keys())],
        y=[dist[k] for k in sorted(dist.keys())],
        marker_color="#6d6fd6",
    ))
    fig_dist.update_layout(template="plotly_white", title="Distribution score de risque")

    fig_shap = go.Figure()
    if shap_imp:
        fig_shap.add_trace(go.Bar(
            x=[s["importance"] for s in shap_imp],
            y=[s["feature"]    for s in shap_imp],
            orientation="h",
            marker_color="#e74c3c",
        ))
        fig_shap.update_layout(
            template="plotly_white",
            title="Top 10 facteurs de risque (SHAP)",
            yaxis={"autorange": "reversed"},
        )

    response = {
        "taux_risque":        round(at_risk / total * 100, 1),
        "nb_clients_risque":  at_risk,
        "total_clients":      total,
        "score_distribution": [{"score": s, "count": c} for s, c in sorted(dist.items())],
        "top_factors":        top_factors,
        "shap_importance":    shap_imp,
        "recommendations":    recommendations,
        "plotly_figures":     {
            "risk_distribution": _figure_json(fig_dist),
            "shap_importance":   _figure_json(fig_shap),
        },
    }
    return _to_serializable(response)

def decision_support(db: Session, limit: int = 100) -> dict:
    _, model_cache = _get_models(db)

    if model_cache is None or "client_risque" not in model_cache:
        return {"clients": [], "plotly_figures": {}, "message": "Models not yet trained. Try again later."}

    b            = model_cache["client_risque"]
    model        = b["model"]
    X_test       = b["X_test"]
    shap_values  = b["shap_values"]

    probas = model.predict_proba(X_test)[:, 1]

    def _niveau_risque(prob: float) -> str:
        if prob >= 0.75:
            return "Critique"
        if prob >= 0.5:
            return "Élevé"
        if prob >= 0.25:
            return "Modéré"
        return "Faible"

    def _priorite_operationnelle(prob: float, nb_actions: int) -> str:
        score = prob + min(nb_actions, 3) * 0.02
        if score >= 0.82:
            return "P1 - Immédiate"
        if score >= 0.6:
            return "P2 - Haute"
        if score >= 0.35:
            return "P3 - Standard"
        return "P4 - Surveillance"

    results = []
    for i, (idx, proba) in enumerate(zip(X_test.index, probas)):
        if i >= limit:
            break

        row_series = X_test.iloc[i]

        top_causes = _get_shap_explanation(shap_values, X_test, i, top_n=5)
        recs       = _generer_recommandations(row_series)
        actions    = _prioriser_actions(recs, float(proba))
        cause_principale = top_causes[0] if top_causes else "Non déterminée"
        action_recommandee = actions[0]["action"] if actions else "Surveillance standard"

        results.append({
            "client_id":  int(idx),
            "risque":     round(float(proba), 3),
            "niveau_risque": _niveau_risque(float(proba)),
            "cause_principale": cause_principale,
            "action_recommandee": action_recommandee,
            "priorite_operationnelle": _priorite_operationnelle(float(proba), len(actions)),
            "top_causes": top_causes,
            "top_actions": actions,
        })

    df_dash = pd.DataFrame([
        {
            "client_id":  r["client_id"],
            "risque":     r["risque"],
            "niveau_risque": r["niveau_risque"],
            "cause_principale": r["cause_principale"],
            "action_recommandee": r["action_recommandee"],
            "priorite_operationnelle": r["priorite_operationnelle"],
            "top_causes": " | ".join(r["top_causes"]),
            "top_actions": " — ".join(a["action"] for a in r["top_actions"]),
        }
        for r in results
    ])

    fig = go.Figure(data=[go.Table(
        header=dict(values=["Client ID", "Risque", "Causes", "Actions"], fill_color="#6d6fd6", font=dict(color="white")),
        cells=dict(
            values=[df_dash[c].tolist() for c in ["client_id", "risque", "top_causes", "top_actions"]],
            fill_color="lavender",
        ),
    )])
    fig.update_layout(title="Système d'aide à la décision — Clients à risque")

    response = {
        "clients":        results,
        "plotly_figures": {"decision_table": _figure_json(fig)},
    }
    return _to_serializable(response)