from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import User
from app.dependencies import get_db, require_roles
from app.services.analytics import init_training_background, list_models, predict


router = APIRouter(prefix="/ml-predictions", tags=["ml-predictions"])


class PredictionRequest(BaseModel):
    model_name: str = Field(..., description="Nom du modèle à utiliser")
    features: dict[str, object] = Field(default_factory=dict, description="Valeurs saisies par l'utilisateur")


@router.get("/models")
def get_models(db: Session = Depends(get_db), _: User = Depends(require_roles("directeur", "admin"))):
    return list_models(db)


@router.get("/health")
def health(_: User = Depends(require_roles("directeur", "admin"))):
    return {"status": "ok", "service": "ml-predictions"}


@router.post("/init")
def init_models(_: User = Depends(require_roles("directeur", "admin"))):
    init_training_background()
    return {"status": "started", "service": "ml-predictions", "mode": "background"}


@router.post("/predict")
def make_prediction(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("directeur", "admin")),
):
    try:
        return predict(db, payload.model_name, payload.features)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {exc}") from exc
