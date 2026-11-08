from __future__ import annotations

import random
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import InstallationProduitCNI, Product, User


GOUVERNORATS = [
    "Tunis", "Ariana", "Ben Arous", "Manouba", "Sfax", "Sousse", "Monastir", "Nabeul",
    "Bizerte", "Mahdia", "Kairouan", "Gabes", "Zaghouan", "Beja", "Siliana", "Le Kef",
    "Tozeur", "Gafsa", "Jendouba", "Kasserine", "Sidi Bouzid", "Medenine", "Tataouine", "Kebili",
]
TYPE_CLIENTS = ["Collectivite locale", "EPA", "EPNA", "Ministere"]
SYSTEMES_EXPLOITATION = ["Windows 10", "Windows 11", "Windows Server 2019", "Windows Server 2022"]
MODES_INSTALLATION = ["Technicien_sur_site", "Telemaintenance"]
REMARKS_FAIL = [
    "version incompatible",
    "poste obsolete",
    "probleme adressage ip",
    "manque espace disque",
    "connexion serveur lente",
    "erreur configuration poste",
    "probleme reseau",
]


def create_installation_record(
    db: Session,
    user: User,
    product: Product,
    version: str,
    previous_version: str,
    force_success: bool = True,
) -> InstallationProduitCNI:
    # Generate next ID manually since legacy DB might not have auto-increment
    max_id_result = db.execute(select(func.max(InstallationProduitCNI.id))).scalar()
    next_id = (max_id_result or 0) + 1
    
    debit = round(random.uniform(8, 120), 2)
    essais = 1 if force_success else random.randint(1, 4)
    success = "oui" if force_success or random.random() > 0.2 else "non"
    satisfied = "oui" if success == "oui" and random.random() > 0.15 else "non"
    complained = "oui" if satisfied == "non" and random.random() > 0.2 else "non"
    duration = round(random.uniform(25, 130), 1)
    taille_site = random.randint(3, 50)
    os_name = random.choice(SYSTEMES_EXPLOITATION)

    installation = InstallationProduitCNI(
        id=next_id,  # Set ID explicitly
        nom_produit=product.name,
        version_produit=version,
        date_installation=date.today(),
        gouvernorat=random.choice(GOUVERNORATS),
        id_client=f"C{user.id:05d}",
        type_client=random.choice(TYPE_CLIENTS),
        systeme_exploitation_poste=os_name,
        installation_reussie=success,
        nombre_essais_installation=essais,
        client_a_reclame=complained,
        nombre_reclamations_client=(0 if complained == "non" else random.randint(1, 4)),
        client_satisfait=satisfied,
        remarques="Aucune" if success == "oui" else random.choice(REMARKS_FAIL),
        technicien_id=f"TECH_{random.randint(1, 120):03d}",
        duree_installation_minutes=duration,
        debit_reseau_mbps=debit,
        taille_site_postes=taille_site,
        mode_installation=random.choice(MODES_INSTALLATION),
        tentative_installation_weekend=random.choice(["oui", "non"]),
        version_precedente=previous_version,
    )
    db.add(installation)
    db.flush()
    return installation
