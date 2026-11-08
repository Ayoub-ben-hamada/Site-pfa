from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from app.dependencies import get_db, require_roles


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db), _: User = Depends(require_roles("directeur", "admin"))):
    from app.services.analytics import dashboard_kpis
    return dashboard_kpis(db)


@router.get("/target/{variable}")
def get_target(variable: str, db: Session = Depends(get_db), _: User = Depends(require_roles("directeur", "admin"))):
    from app.services.analytics import target_analysis
    return target_analysis(db, variable)


@router.get("/predictions")
def get_predictions(db: Session = Depends(get_db), _: User = Depends(require_roles("directeur", "admin"))):
    from app.services.analytics import predictions
    return predictions(db)


@router.get("/risk-analysis")
def get_risk(db: Session = Depends(get_db), _: User = Depends(require_roles("directeur", "admin"))):
    from app.services.analytics import risk_analysis
    return risk_analysis(db)


@router.get("/decision-support")
def get_decision_support(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("directeur", "admin"))
):
    from app.services.analytics import decision_support
    return decision_support(db, limit=limit)
