from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Notification, Product, User, UserProductPermission
from app.dependencies import get_db, require_roles
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.user import PermissionUpdate, UserCreate, UserUpdate
from app.services.installations import create_installation_record
from app.services.analytics import clear_target_analysis_cache


router = APIRouter(prefix="/admin", tags=["admin"])
permissions_router = APIRouter(tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    users = db.scalars(select(User)).all()
    output = []
    for u in users:
        products = db.scalars(
            select(UserProductPermission.product_id).where(UserProductPermission.user_id == u.id)
        ).all()
        output.append(
            {
                "id": u.id,
                "email": u.email,
                "name": u.full_name,
                "role": u.role,
                "organization": u.organization,
                "products": products,
            }
        )
    return output


@router.post("/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email deja utilise")

    user = User(
        email=payload.email,
        full_name=payload.name,
        role=payload.role,
        organization=payload.organization,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    _sync_user_products(db=db, user=user, new_product_ids=payload.products)

    db.commit()
    clear_target_analysis_cache()
    return {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "role": user.role,
        "organization": user.organization,
        "products": payload.products,
    }


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if payload.name is not None:
        user.full_name = payload.name
    if payload.role is not None:
        user.role = payload.role
    if payload.organization is not None:
        user.organization = payload.organization
    if payload.products is not None:
        _sync_user_products(db=db, user=user, new_product_ids=payload.products)

    db.commit()
    clear_target_analysis_cache()

    products = db.scalars(
        select(UserProductPermission.product_id).where(UserProductPermission.user_id == user.id)
    ).all()
    return {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "role": user.role,
        "organization": user.organization,
        "products": products,
    }


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprime"}


@router.get("/products")
def list_products(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    items = db.scalars(select(Product)).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "latest_version": p.latest_version,
            "category": p.category,
        }
        for p in items
    ]


@router.post("/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    if db.scalar(select(Product).where(Product.name == payload.name)):
        raise HTTPException(status_code=400, detail="Nom produit deja utilise")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "latest_version": product.latest_version,
        "category": product.category,
    }


@router.put("/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "latest_version": product.latest_version,
        "category": product.category,
    }


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    db.delete(product)
    db.commit()
    return {"message": "Produit supprime"}


@router.put("/permissions")
def update_permissions(payload: PermissionUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    user = db.get(User, payload.user_id)
    product = db.get(Product, payload.product_id)
    if not user or not product:
        raise HTTPException(status_code=404, detail="Utilisateur ou produit introuvable")

    perm = db.scalar(
        select(UserProductPermission).where(
            UserProductPermission.user_id == payload.user_id,
            UserProductPermission.product_id == payload.product_id,
        )
    )

    if not perm:
        perm = UserProductPermission(user_id=payload.user_id, product_id=payload.product_id)
        db.add(perm)

    perm.can_view = payload.can_view
    perm.can_update = payload.can_update
    perm.allowed_features = payload.allowed_features

    db.commit()
    clear_target_analysis_cache()
    return {
        "message": "Permissions mises a jour",
        "user_id": payload.user_id,
        "product_id": payload.product_id,
        "can_view": perm.can_view,
        "can_update": perm.can_update,
        "allowed_features": perm.allowed_features,
    }


@router.get("/permissions")
def get_permissions(
    user_id: int = Query(...),
    product_id: int = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    product = db.get(Product, product_id)
    if not user or not product:
        raise HTTPException(status_code=404, detail="Utilisateur ou produit introuvable")

    perm = db.scalar(
        select(UserProductPermission).where(
            UserProductPermission.user_id == user_id,
            UserProductPermission.product_id == product_id,
        )
    )

    if not perm:
        return {
            "user_id": user_id,
            "product_id": product_id,
            "can_view": False,
            "can_update": False,
            "allowed_features": [],
        }

    return {
        "user_id": user_id,
        "product_id": product_id,
        "can_view": perm.can_view,
        "can_update": perm.can_update,
        "allowed_features": perm.allowed_features,
    }


@permissions_router.put("/permissions")
def update_permissions_root(payload: PermissionUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return update_permissions(payload, db, _)


def _sync_user_products(db: Session, user: User, new_product_ids: list[int]) -> None:
    existing = db.scalars(
        select(UserProductPermission).where(UserProductPermission.user_id == user.id)
    ).all()

    existing_ids = {p.product_id for p in existing}
    wanted = set(new_product_ids)

    for perm in existing:
        if perm.product_id not in wanted:
            db.delete(perm)

    for product_id in wanted - existing_ids:
        product = db.get(Product, product_id)
        if not product:
            continue

        perm = UserProductPermission(
            user_id=user.id,
            product_id=product_id,
            can_view=True,
            can_update=True,
            allowed_features=["download", "install", "update", "history"],
        )
        db.add(perm)

        create_installation_record(
            db=db,
            user=user,
            product=product,
            version="1.0",
            previous_version="0",
            force_success=True,
        )
        db.add(
            Notification(
                user_id=user.id,
                type="info",
                title=f"Produit ajoute: {product.name}",
                message="Votre licence est active, vous pouvez installer le produit.",
            )
        )
