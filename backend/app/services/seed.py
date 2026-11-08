from __future__ import annotations

import random

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import InstallationProduitCNI, Notification, Product, User, UserProductPermission
from app.services.analytics import clear_target_analysis_cache
from app.services.installations import create_installation_record


DEMO_USERS = [
    {
        "email": "client@demo.com",
        "full_name": "Client Demo",
        "role": "client",
        "organization": "Ministere Test",
        "password": "demo123",
    },
    {
        "email": "admin@demo.com",
        "full_name": "Admin Demo",
        "role": "admin",
        "organization": "CNI",
        "password": "demo123",
    },
    {
        "email": "directeur@demo.com",
        "full_name": "Directeur Demo",
        "role": "directeur",
        "organization": "CNI",
        "password": "demo123",
    },
]

DEFAULT_PRODUCTS = [
    {
        "name": "GRB",
        "description": "Gestion des Ressources Budgetaires",
        "latest_version": "3.0",
        "category": "Finance",
    },
    {
        "name": "MADANIA",
        "description": "Systeme de gestion de l'etat civil",
        "latest_version": "3.0",
        "category": "Administration",
    },
    {
        "name": "MAKATIB",
        "description": "Gestion du courrier administratif",
        "latest_version": "3.0",
        "category": "Communication",
    },
    {
        "name": "INSAF",
        "description": "Systeme de gestion des affaires sociales",
        "latest_version": "3.0",
        "category": "Social",
    },
]


def _repair_installation_ids(db: Session) -> None:
    null_ids = db.scalar(
        text("select count(*) from installations_produits_cni where id is null")
    )
    if not null_ids:
        return

    db.execute(text(
        """
        with numbered as (
            select ctid, row_number() over (order by ctid) as new_id
            from installations_produits_cni
            where id is null
        )
        update installations_produits_cni t
        set id = numbered.new_id + coalesce((select max(id) from installations_produits_cni where id is not null), 0)
        from numbered
        where t.ctid = numbered.ctid
        """
    ))
    db.execute(text(
        """
        do $$
        declare
            max_id bigint;
        begin
            select coalesce(max(id), 0) into max_id from installations_produits_cni;
            execute format('select setval(pg_get_serial_sequence(''installations_produits_cni'', ''id''), %s, true)', max_id);
        end $$;
        """
    ))


def seed_demo_data(db: Session) -> None:
    _repair_installation_ids(db)

    created_users: dict[str, User] = {}
    for row in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == row["email"]))
        if user is None:
            user = User(
                email=row["email"],
                full_name=row["full_name"],
                role=row["role"],
                organization=row["organization"],
                hashed_password=hash_password(row["password"]),
            )
            db.add(user)
            db.flush()
        created_users[user.email] = user

    created_products: list[Product] = []
    for row in DEFAULT_PRODUCTS:
        product = db.scalar(select(Product).where(Product.name == row["name"]))
        if product is None:
            product = Product(**row)
            db.add(product)
            db.flush()
        created_products.append(product)

    client = created_users["client@demo.com"]
    for product in created_products[:2]:
        perm_exists = db.scalar(
            select(UserProductPermission.id).where(
                UserProductPermission.user_id == client.id,
                UserProductPermission.product_id == product.id,
            )
        )
        if not perm_exists:
            perm = UserProductPermission(
                user_id=client.id,
                product_id=product.id,
                can_view=True,
                can_update=True,
                allowed_features=["download", "install", "update", "history"],
            )
            db.add(perm)

    installations_exist = db.scalar(select(InstallationProduitCNI.id).limit(1))
    if not installations_exist:
        for product in created_products[:2]:
            create_installation_record(
                db=db,
                user=client,
                product=product,
                version="1.0",
                previous_version="0",
                force_success=True,
            )

        for _ in range(180):
            product = random.choice(created_products)
            create_installation_record(
                db=db,
                user=client,
                product=product,
                version=random.choice(["1.0", "1.1", "2.0", "2.1", "3.0"]),
                previous_version=random.choice(["0", "1.0", "1.1", "2.0"]),
                force_success=random.random() > 0.1,
            )

        db.add(
            Notification(
                user_id=client.id,
                type="info",
                title="Bienvenue sur SADP",
                message="Votre portail applicatif est actif. Consultez vos produits et mises a jour.",
            )
        )

    db.commit()
    clear_target_analysis_cache()
