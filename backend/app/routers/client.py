from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import InstallationProduitCNI, Notification, Product, User, UserProductPermission
from app.dependencies import get_current_user, get_db
from app.schemas.dashboard import UpdateProductRequest
from app.services.installations import create_installation_record
from app.services.analytics import clear_target_analysis_cache


router = APIRouter(tags=["client"])


@router.get("/products")
def get_products(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = db.scalars(
        select(UserProductPermission).where(UserProductPermission.user_id == user.id, UserProductPermission.can_view.is_(True))
    ).all()

    result = []
    for perm in perms:
        product = db.get(Product, perm.product_id)
        if not product:
            continue

        last_install = db.scalar(
            select(InstallationProduitCNI)
            .where(
                InstallationProduitCNI.id_client == f"C{user.id:05d}",
                InstallationProduitCNI.nom_produit == product.name,
            )
            .order_by(desc(InstallationProduitCNI.date_installation), desc(InstallationProduitCNI.id))
            .limit(1)
        )

        history = db.scalars(
            select(InstallationProduitCNI)
            .where(
                InstallationProduitCNI.id_client == f"C{user.id:05d}",
                InstallationProduitCNI.nom_produit == product.name,
            )
            .order_by(desc(InstallationProduitCNI.date_installation), desc(InstallationProduitCNI.id))
            .limit(10)
        ).all()

        installed_version = last_install.version_produit if last_install else "1.0"
        result.append(
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "latest_version": product.latest_version,
                "category": product.category,
                "installed_version": installed_version,
                "install_date": str(last_install.date_installation) if last_install else str(datetime.utcnow().date()),
                "status": "active",
                "update_available": product.latest_version != installed_version,
                "permissions": {
                    "can_view": perm.can_view,
                    "can_update": perm.can_update,
                    "allowed_features": perm.allowed_features,
                },
                "history": [
                    {
                        "id": h.id,
                        "version": h.version_produit,
                        "date": str(h.date_installation),
                        "success": h.installation_reussie,
                    }
                    for h in history
                ],
            }
        )
    return result


@router.post("/update-product")
def update_product_by_body(
    payload: UpdateProductRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _update_product(user=user, product_id=payload.product_id, db=db)


@router.post("/products/{product_id}/update")
def update_product_path(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _update_product(user=user, product_id=product_id, db=db)


def _update_product(user: User, product_id: int, db: Session):
    perm = db.scalar(
        select(UserProductPermission).where(
            UserProductPermission.user_id == user.id,
            UserProductPermission.product_id == product_id,
            UserProductPermission.can_update.is_(True),
        )
    )
    if not perm:
        raise HTTPException(status_code=403, detail="Mise a jour non autorisee pour ce produit")

    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    last_install = db.scalar(
        select(InstallationProduitCNI)
        .where(
            InstallationProduitCNI.id_client == f"C{user.id:05d}",
            InstallationProduitCNI.nom_produit == product.name,
        )
        .order_by(desc(InstallationProduitCNI.date_installation), desc(InstallationProduitCNI.id))
        .limit(1)
    )

    previous = last_install.version_produit if last_install else "1.0"

    installation = create_installation_record(
        db=db,
        user=user,
        product=product,
        version=product.latest_version,
        previous_version=previous,
        force_success=True,
    )

    db.add(
        Notification(
            user_id=user.id,
            type="success",
            title=f"{product.name} mis a jour",
            message=f"Version {previous} vers {product.latest_version}",
        )
    )
    db.commit()
    clear_target_analysis_cache()

    return {
        "message": f"Produit mis a jour vers la version {product.latest_version}",
        "installation": {
            "id": installation.id,
            "Nom_produit": installation.nom_produit,
            "version_produit": installation.version_produit,
            "date_installation": str(installation.date_installation),
        },
    }


@router.get("/notifications")
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(desc(Notification.created_at)).limit(50)
    ).all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "date": n.created_at.isoformat(),
            "read": n.is_read,
        }
        for n in notifications
    ]


@router.get("/client/installations")
def get_installations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(InstallationProduitCNI)
        .where(InstallationProduitCNI.id_client == f"C{user.id:05d}")
        .order_by(desc(InstallationProduitCNI.date_installation), desc(InstallationProduitCNI.id))
        .limit(100)
    ).all()
    return [
        {
            "id": r.id,
            "Nom_produit": r.nom_produit,
            "version_produit": r.version_produit,
            "date_installation": str(r.date_installation),
            "installation_reussie": r.installation_reussie,
            "Duree_installation_minutes": r.duree_installation_minutes,
            "Mode_installation": r.mode_installation,
        }
        for r in rows
    ]
