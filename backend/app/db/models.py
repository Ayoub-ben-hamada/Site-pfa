from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    client = "client"
    admin = "admin"
    directeur = "directeur"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    organization: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_permissions: Mapped[list[UserProductPermission]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(1000))
    latest_version: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions: Mapped[list[UserProductPermission]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class UserProductPermission(Base):
    __tablename__ = "user_product_permissions"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_update: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_features: Mapped[list[str]] = mapped_column(JSON, default=list)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="product_permissions")
    product: Mapped[Product] = relationship(back_populates="permissions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(50), default="info")
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(String(1000))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="notifications")


class InstallationProduitCNI(Base):
    __tablename__ = "installations_produits_cni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_produit: Mapped[str] = mapped_column("Nom_produit", String(120), index=True)
    version_produit: Mapped[str] = mapped_column("version_produit", String(50))
    date_installation: Mapped[datetime] = mapped_column("date_installation", Date)
    gouvernorat: Mapped[str] = mapped_column("Gouvernorat", String(120), index=True)
    id_client: Mapped[str] = mapped_column("Id_Client", String(50), index=True)
    type_client: Mapped[str] = mapped_column("Type_client", String(120))
    systeme_exploitation_poste: Mapped[str] = mapped_column("Systeme_exploitation_poste", String(120))
    installation_reussie: Mapped[str] = mapped_column("installation_reussie", String(10))
    nombre_essais_installation: Mapped[int] = mapped_column("nombre_essais_installation", Integer)
    client_a_reclame: Mapped[str] = mapped_column("client_a_reclame", String(10))
    nombre_reclamations_client: Mapped[int] = mapped_column("nombre_reclamations_client", Integer)
    client_satisfait: Mapped[str] = mapped_column("client_satisfait", String(10))
    remarques: Mapped[str] = mapped_column("Remarques", String(1000))
    technicien_id: Mapped[str] = mapped_column("Technicien_ID", String(50))
    duree_installation_minutes: Mapped[float] = mapped_column("Duree_installation_minutes", Float)
    debit_reseau_mbps: Mapped[float] = mapped_column("Debit_reseau_Mbps", Float)
    taille_site_postes: Mapped[int] = mapped_column("Taille_site_postes", Integer)
    mode_installation: Mapped[str] = mapped_column("Mode_installation", String(80))
    tentative_installation_weekend: Mapped[str] = mapped_column("Tentative_installation_weekend", String(10))
    version_precedente: Mapped[str] = mapped_column("Version_precedente", String(50))

