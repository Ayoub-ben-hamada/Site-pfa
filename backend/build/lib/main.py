import fastapi
import fastapi.middleware.cors
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import json
import random
import numpy as np
from sqlalchemy.orm import Session
from app.db.session import get_db
app = fastapi.FastAPI(title="CNI Analytics API", version="1.0.0")

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "cni-analytics-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()

# Demo users (hardcoded)
DEMO_USERS = {
    "client@demo.com": {"password": "demo123", "role": "client", "name": "Client Demo", "id": 1},
    "admin@demo.com": {"password": "demo123", "role": "admin", "name": "Admin Demo", "id": 2},
    "directeur@demo.com": {"password": "demo123", "role": "directeur", "name": "Directeur Demo", "id": 3},
}

# Sample products catalog
PRODUCTS_CATALOG = [
    {"id": 1, "name": "GRB", "description": "Gestion des Ressources Budgétaires - Solution de gestion budgétaire", "latest_version": "3.0", "category": "Finance"},
    {"id": 2, "name": "MADANIA", "description": "Système de gestion de l'état civil", "latest_version": "3.0", "category": "Administration"},
    {"id": 3, "name": "MAKATIB", "description": "Gestion du courrier administratif", "latest_version": "3.0", "category": "Communication"},
    {"id": 4, "name": "INSAF", "description": "Système de gestion des affaires sociales", "latest_version": "3.0", "category": "Social"},
]

# Sample users database
USERS_DB = [
    {"id": 1, "email": "client@demo.com", "name": "Client Demo", "role": "client", "organization": "Ministère Test", "products": [1, 2]},
    {"id": 2, "email": "admin@demo.com", "name": "Admin Demo", "role": "admin", "organization": "CNI", "products": []},
    {"id": 3, "email": "directeur@demo.com", "name": "Directeur Demo", "role": "directeur", "organization": "CNI", "products": []},
    {"id": 4, "email": "user1@test.com", "name": "Utilisateur Test 1", "role": "client", "organization": "EPA Tunis", "products": [1, 3]},
    {"id": 5, "email": "user2@test.com", "name": "Utilisateur Test 2", "role": "client", "organization": "EPNA Sfax", "products": [2, 4]},
]

# Sample installations data
GOUVERNORATS = ["Tunis", "Ariana", "Ben Arous", "Manouba", "Sfax", "Sousse", "Monastir", "Nabeul", "Bizerte", "Mahdia", "Kairouan", "Gabès", "Zaghouan", "Béja", "Siliana", "Le Kef", "Tozeur", "Gafsa", "Jendouba", "Kasserine", "Sidi Bouzid", "Médenine", "Tataouine", "Kébili"]
TYPE_CLIENTS = ["Collectivité locale", "EPA", "EPNA", "Ministère"]
SYSTEMES_EXPLOITATION = ["Win10", "Win11", "Windows server 2022", "Windows server 2019", "Windows server 2016", "Win8", "Win7"]
MODES_INSTALLATION = ["Technicien_sur_site", "Télémaintenance"]
REMARQUES_OPTIONS = ["version incompatible", "poste obsolète", "Problème adressage ip", "manque espace disque", "connexion serveur lente", "erreur configuration poste", "problème réseau", "Aucune"]

def generate_sample_installations(count=500):
    installations = []
    for i in range(count):
        product = random.choice(PRODUCTS_CATALOG)
        version = random.choice(["1.0", "1.1", "1.2", "2.0", "2.1", "2.2", "3.0"])
        reussie = random.choice(["oui", "non"])
        satisfait = "oui" if reussie == "oui" and random.random() > 0.3 else "non"
        reclame = "non" if satisfait == "oui" else random.choice(["oui", "non"])
        
        base_date = datetime(2020, 1, 1)
        random_days = random.randint(0, 1800)
        install_date = base_date + timedelta(days=random_days)
        
        debit = round(random.uniform(2, 100), 2)
        duree = 30 if reussie == "oui" and debit > 20 else random.randint(60, 180)
        
        installations.append({
            "id": i + 1,
            "Nom_produit": product["name"],
            "version_produit": version,
            "date_installation": install_date.strftime("%Y-%m-%d"),
            "Gouvernorat": random.choice(GOUVERNORATS),
            "Id_Client": f"C{random.randint(10000, 99999)}",
            "Type_client": random.choice(TYPE_CLIENTS),
            "Systeme_exploitation_poste": random.choice(SYSTEMES_EXPLOITATION),
            "installation_reussie": reussie,
            "nombre_essais_installation": random.randint(1, 5),
            "client_a_reclame": reclame,
            "nombre_reclamations_client": random.randint(0, 4) if reclame == "oui" else 0,
            "client_satisfait": satisfait,
            "Remarques": "Aucune" if reussie == "oui" and satisfait == "oui" else random.choice(REMARQUES_OPTIONS[:-1]),
            "Technicien_ID": f"TECH_{random.randint(1, 50):03d}",
            "Duree_installation_minutes": duree,
            "Debit_reseau_Mbps": debit,
            "Taille_site_postes": random.randint(1, 30),
            "Mode_installation": random.choice(MODES_INSTALLATION),
            "Tentative_installation_weekend": random.choice(["oui", "non"]),
            "Version_precedente": random.choice(["0", "0.9", "1.0", "1.1", "1.2", "2.0"]),
        })
    return installations

INSTALLATIONS_DB = generate_sample_installations(500)

# Client product assignments
CLIENT_PRODUCTS = {
    1: [
        {"product_id": 1, "installed_version": "2.1", "install_date": "2024-01-15", "status": "active"},
        {"product_id": 2, "installed_version": "1.2", "install_date": "2023-11-20", "status": "active"},
    ],
    4: [
        {"product_id": 1, "installed_version": "2.0", "install_date": "2024-02-10", "status": "active"},
        {"product_id": 3, "installed_version": "2.2", "install_date": "2024-03-05", "status": "active"},
    ],
    5: [
        {"product_id": 2, "installed_version": "2.1", "install_date": "2024-01-25", "status": "active"},
        {"product_id": 4, "installed_version": "1.1", "install_date": "2023-12-15", "status": "active"},
    ],
}

# Pydantic Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    email: str
    name: str
    role: str
    organization: str
    products: list[int] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    products: Optional[list[int]] = None

class ProductCreate(BaseModel):
    name: str
    description: str
    latest_version: str
    category: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latest_version: Optional[str] = None
    category: Optional[str] = None

# Helper functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"email": email, "role": role, "user_id": payload.get("user_id")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

def require_role(allowed_roles: list):
    def role_checker(current_user: dict = Depends(verify_token)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        return current_user
    return role_checker

# AUTH ENDPOINTS
@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = DEMO_USERS.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    access_token = create_access_token(
        data={"sub": request.email, "role": user["role"], "user_id": user["id"]}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": request.email, "role": user["role"], "name": user["name"], "id": user["id"]}
    }

@app.get("/me")
async def get_current_user(current_user: dict = Depends(verify_token)):
    user_data = DEMO_USERS.get(current_user["email"])
    if not user_data:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {
        "email": current_user["email"],
        "role": current_user["role"],
        "name": user_data["name"],
        "id": user_data["id"]
    }

# CLIENT ENDPOINTS
@app.get("/products")
async def get_client_products(current_user: dict = Depends(verify_token)):
    user_id = current_user["user_id"]
    user_products = CLIENT_PRODUCTS.get(user_id, [])
    
    result = []
    for up in user_products:
        product = next((p for p in PRODUCTS_CATALOG if p["id"] == up["product_id"]), None)
        if product:
            result.append({
                **product,
                "installed_version": up["installed_version"],
                "install_date": up["install_date"],
                "status": up["status"],
                "update_available": product["latest_version"] != up["installed_version"]
            })
    return result

@app.post("/products/{product_id}/update")
async def update_product(product_id: int, current_user: dict = Depends(verify_token)):
    user_id = current_user["user_id"]
    user_products = CLIENT_PRODUCTS.get(user_id, [])
    
    product = next((p for p in PRODUCTS_CATALOG if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    for up in user_products:
        if up["product_id"] == product_id:
            old_version = up["installed_version"]
            up["installed_version"] = product["latest_version"]
            up["install_date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Create installation record
            new_install = {
                "id": len(INSTALLATIONS_DB) + 1,
                "Nom_produit": product["name"],
                "version_produit": product["latest_version"],
                "date_installation": datetime.now().strftime("%Y-%m-%d"),
                "Gouvernorat": random.choice(GOUVERNORATS),
                "Id_Client": f"C{user_id:05d}",
                "Type_client": random.choice(TYPE_CLIENTS),
                "Systeme_exploitation_poste": random.choice(SYSTEMES_EXPLOITATION),
                "installation_reussie": "oui",
                "nombre_essais_installation": 1,
                "client_a_reclame": "non",
                "nombre_reclamations_client": 0,
                "client_satisfait": "oui",
                "Remarques": "Aucune",
                "Technicien_ID": f"TECH_{random.randint(1, 50):03d}",
                "Duree_installation_minutes": random.randint(20, 45),
                "Debit_reseau_Mbps": round(random.uniform(20, 100), 2),
                "Taille_site_postes": random.randint(5, 20),
                "Mode_installation": "Télémaintenance",
                "Tentative_installation_weekend": "non",
                "Version_precedente": old_version,
            }
            INSTALLATIONS_DB.append(new_install)
            
            return {"message": f"Produit mis à jour vers la version {product['latest_version']}", "installation": new_install}
    
    raise HTTPException(status_code=404, detail="Produit non attribué à cet utilisateur")

@app.get("/notifications")
async def get_notifications(current_user: dict = Depends(verify_token)):
    user_id = current_user["user_id"]
    user_products = CLIENT_PRODUCTS.get(user_id, [])
    
    notifications = []
    for up in user_products:
        product = next((p for p in PRODUCTS_CATALOG if p["id"] == up["product_id"]), None)
        if product and product["latest_version"] != up["installed_version"]:
            notifications.append({
                "id": len(notifications) + 1,
                "type": "update",
                "title": f"Mise à jour disponible pour {product['name']}",
                "message": f"Version {product['latest_version']} disponible (installée: {up['installed_version']})",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "read": False
            })
    
    return notifications

@app.get("/client/installations")
async def get_client_installations(current_user: dict = Depends(verify_token)):
    user_id = current_user["user_id"]
    client_id = f"C{user_id:05d}"
    
    installations = [i for i in INSTALLATIONS_DB if i["Id_Client"] == client_id]
    return installations[-10:]  # Return last 10 installations

# ADMIN ENDPOINTS
@app.get("/admin/users")
async def get_all_users(current_user: dict = Depends(require_role(["admin"]))):
    return USERS_DB

@app.post("/admin/users")
async def create_user(user: UserCreate, current_user: dict = Depends(require_role(["admin"]))):
    new_id = max(u["id"] for u in USERS_DB) + 1
    new_user = {
        "id": new_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization": user.organization,
        "products": user.products
    }
    USERS_DB.append(new_user)
    
    # Initialize product assignments for new client
    if user.role == "client" and user.products:
        CLIENT_PRODUCTS[new_id] = [
            {
                "product_id": pid,
                "installed_version": "1.0",
                "install_date": datetime.now().strftime("%Y-%m-%d"),
                "status": "active"
            }
            for pid in user.products
        ]
        
        # Create installation records for each product
        for pid in user.products:
            product = next((p for p in PRODUCTS_CATALOG if p["id"] == pid), None)
            if product:
                new_install = {
                    "id": len(INSTALLATIONS_DB) + 1,
                    "Nom_produit": product["name"],
                    "version_produit": "1.0",
                    "date_installation": datetime.now().strftime("%Y-%m-%d"),
                    "Gouvernorat": random.choice(GOUVERNORATS),
                    "Id_Client": f"C{new_id:05d}",
                    "Type_client": random.choice(TYPE_CLIENTS),
                    "Systeme_exploitation_poste": random.choice(SYSTEMES_EXPLOITATION),
                    "installation_reussie": "oui",
                    "nombre_essais_installation": 1,
                    "client_a_reclame": "non",
                    "nombre_reclamations_client": 0,
                    "client_satisfait": "oui",
                    "Remarques": "Aucune",
                    "Technicien_ID": f"TECH_{random.randint(1, 50):03d}",
                    "Duree_installation_minutes": random.randint(25, 60),
                    "Debit_reseau_Mbps": round(random.uniform(15, 80), 2),
                    "Taille_site_postes": random.randint(3, 25),
                    "Mode_installation": random.choice(MODES_INSTALLATION),
                    "Tentative_installation_weekend": "non",
                    "Version_precedente": "0",
                }
                INSTALLATIONS_DB.append(new_install)
    
    # Add to demo users for login
    DEMO_USERS[user.email] = {"password": "demo123", "role": user.role, "name": user.name, "id": new_id}
    
    return new_user

@app.put("/admin/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(require_role(["admin"]))):
    user = next((u for u in USERS_DB if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user_update.name:
        user["name"] = user_update.name
    if user_update.role:
        user["role"] = user_update.role
    if user_update.organization:
        user["organization"] = user_update.organization
    if user_update.products is not None:
        old_products = set(user["products"])
        new_products = set(user_update.products)
        user["products"] = user_update.products
        
        # Update client products
        if user["role"] == "client":
            current_assignments = CLIENT_PRODUCTS.get(user_id, [])
            current_product_ids = {cp["product_id"] for cp in current_assignments}
            
            # Add new products
            for pid in new_products - current_product_ids:
                product = next((p for p in PRODUCTS_CATALOG if p["id"] == pid), None)
                if product:
                    current_assignments.append({
                        "product_id": pid,
                        "installed_version": "1.0",
                        "install_date": datetime.now().strftime("%Y-%m-%d"),
                        "status": "active"
                    })
                    # Create installation record
                    new_install = {
                        "id": len(INSTALLATIONS_DB) + 1,
                        "Nom_produit": product["name"],
                        "version_produit": "1.0",
                        "date_installation": datetime.now().strftime("%Y-%m-%d"),
                        "Gouvernorat": random.choice(GOUVERNORATS),
                        "Id_Client": f"C{user_id:05d}",
                        "Type_client": random.choice(TYPE_CLIENTS),
                        "Systeme_exploitation_poste": random.choice(SYSTEMES_EXPLOITATION),
                        "installation_reussie": "oui",
                        "nombre_essais_installation": 1,
                        "client_a_reclame": "non",
                        "nombre_reclamations_client": 0,
                        "client_satisfait": "oui",
                        "Remarques": "Aucune",
                        "Technicien_ID": f"TECH_{random.randint(1, 50):03d}",
                        "Duree_installation_minutes": random.randint(25, 60),
                        "Debit_reseau_Mbps": round(random.uniform(15, 80), 2),
                        "Taille_site_postes": random.randint(3, 25),
                        "Mode_installation": random.choice(MODES_INSTALLATION),
                        "Tentative_installation_weekend": "non",
                        "Version_precedente": "0",
                    }
                    INSTALLATIONS_DB.append(new_install)
            
            CLIENT_PRODUCTS[user_id] = current_assignments
    
    return user

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_role(["admin"]))):
    global USERS_DB
    user = next((u for u in USERS_DB if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    USERS_DB = [u for u in USERS_DB if u["id"] != user_id]
    if user["email"] in DEMO_USERS:
        del DEMO_USERS[user["email"]]
    if user_id in CLIENT_PRODUCTS:
        del CLIENT_PRODUCTS[user_id]
    
    return {"message": "Utilisateur supprimé"}

@app.get("/admin/products")
async def get_all_products(current_user: dict = Depends(require_role(["admin"]))):
    return PRODUCTS_CATALOG

@app.post("/admin/products")
async def create_product(product: ProductCreate, current_user: dict = Depends(require_role(["admin"]))):
    new_id = max(p["id"] for p in PRODUCTS_CATALOG) + 1
    new_product = {
        "id": new_id,
        "name": product.name,
        "description": product.description,
        "latest_version": product.latest_version,
        "category": product.category
    }
    PRODUCTS_CATALOG.append(new_product)
    return new_product

@app.put("/admin/products/{product_id}")
async def update_product_admin(product_id: int, product_update: ProductUpdate, current_user: dict = Depends(require_role(["admin"]))):
    product = next((p for p in PRODUCTS_CATALOG if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    if product_update.name:
        product["name"] = product_update.name
    if product_update.description:
        product["description"] = product_update.description
    if product_update.latest_version:
        product["latest_version"] = product_update.latest_version
    if product_update.category:
        product["category"] = product_update.category
    
    return product

@app.delete("/admin/products/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(require_role(["admin"]))):
    global PRODUCTS_CATALOG
    product = next((p for p in PRODUCTS_CATALOG if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    PRODUCTS_CATALOG = [p for p in PRODUCTS_CATALOG if p["id"] != product_id]
    return {"message": "Produit supprimé"}

# DASHBOARD ENDPOINTS (Director)
@app.get("/dashboard/kpis")
async def get_dashboard_kpis(current_user: dict = Depends(require_role(["directeur", "admin"]))):
    total_installations = len(INSTALLATIONS_DB)
    reussies = sum(1 for i in INSTALLATIONS_DB if i["installation_reussie"] == "oui")
    satisfaits = sum(1 for i in INSTALLATIONS_DB if i["client_satisfait"] == "oui")
    reclame = sum(1 for i in INSTALLATIONS_DB if i["client_a_reclame"] == "oui")
    
    durees = [i["Duree_installation_minutes"] for i in INSTALLATIONS_DB]
    essais = [i["nombre_essais_installation"] for i in INSTALLATIONS_DB]
    debits = [i["Debit_reseau_Mbps"] for i in INSTALLATIONS_DB]
    
    # Calculate risk score for each installation
    def calc_risk(inst):
        score = 0
        if inst["Debit_reseau_Mbps"] < 5:
            score += 1
        if inst["nombre_essais_installation"] > 2:
            score += 1
        if inst["Duree_installation_minutes"] > 120:
            score += 1
        if inst["Systeme_exploitation_poste"] in ["WindowsXP", "Win7", "Win8"]:
            score += 1
        if inst["Nom_produit"] == "GRB":
            score += 1
        if inst["Gouvernorat"] in ["Gafsa", "Jendouba", "Kasserine", "Médenine", "Tataouine"]:
            score += 1
        return score >= 3
    
    clients_risque = sum(1 for i in INSTALLATIONS_DB if calc_risk(i))
    
    # Alerts
    alerts = []
    taux_reussite = reussies / total_installations if total_installations > 0 else 0
    if taux_reussite < 0.7:
        alerts.append({"type": "warning", "message": f"Taux de réussite faible: {taux_reussite*100:.1f}%"})
    
    taux_risque = clients_risque / total_installations if total_installations > 0 else 0
    if taux_risque > 0.3:
        alerts.append({"type": "danger", "message": f"Taux de clients à risque élevé: {taux_risque*100:.1f}%"})
    
    taux_reclamation = reclame / total_installations if total_installations > 0 else 0
    if taux_reclamation > 0.4:
        alerts.append({"type": "warning", "message": f"Taux de réclamation élevé: {taux_reclamation*100:.1f}%"})
    
    avg_duree = sum(durees) / len(durees) if durees else 0
    if avg_duree > 90:
        alerts.append({"type": "info", "message": f"Durée moyenne d'installation élevée: {avg_duree:.0f} min"})
    
    return {
        "nb_installations": total_installations,
        "taux_reussite": round(taux_reussite * 100, 1),
        "taux_satisfaction": round(satisfaits / total_installations * 100, 1) if total_installations > 0 else 0,
        "taux_reclamation": round(taux_reclamation * 100, 1),
        "duree_moyenne": round(avg_duree, 1),
        "nb_moyen_essais": round(sum(essais) / len(essais), 2) if essais else 0,
        "taux_clients_risque": round(taux_risque * 100, 1),
        "debit_moyen": round(sum(debits) / len(debits), 2) if debits else 0,
        "alerts": alerts
    }

@app.get("/dashboard/target/{variable}")
async def get_target_analysis(variable: str, current_user: dict = Depends(require_role(["directeur", "admin"]))):
    valid_variables = ["installation_reussie", "client_satisfait", "client_a_reclame", "Duree_installation_minutes", "nombre_essais_installation"]
    if variable not in valid_variables:
        raise HTTPException(status_code=400, detail=f"Variable invalide. Choisir parmi: {valid_variables}")
    
    # Group by month
    monthly_data = {}
    for inst in INSTALLATIONS_DB:
        month = inst["date_installation"][:7]  # YYYY-MM
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(inst)
    
    # Calculate metrics per month
    temporal_data = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"]:
            value = sum(1 for d in data if d[variable] == "oui") / len(data) if data else 0
        else:
            values = [d[variable] for d in data]
            value = sum(values) / len(values) if values else 0
        temporal_data.append({"month": month, "value": round(value, 3) if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"] else round(value, 1)})
    
    # Distribution by product
    product_data = {}
    for inst in INSTALLATIONS_DB:
        prod = inst["Nom_produit"]
        if prod not in product_data:
            product_data[prod] = []
        product_data[prod].append(inst)
    
    by_product = []
    for prod, data in product_data.items():
        if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"]:
            value = sum(1 for d in data if d[variable] == "oui") / len(data) if data else 0
        else:
            values = [d[variable] for d in data]
            value = sum(values) / len(values) if values else 0
        by_product.append({"product": prod, "value": round(value * 100, 1) if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"] else round(value, 1)})
    
    # Distribution by gouvernorat
    gouv_data = {}
    for inst in INSTALLATIONS_DB:
        gouv = inst["Gouvernorat"]
        if gouv not in gouv_data:
            gouv_data[gouv] = []
        gouv_data[gouv].append(inst)
    
    by_gouvernorat = []
    for gouv, data in gouv_data.items():
        if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"]:
            value = sum(1 for d in data if d[variable] == "oui") / len(data) if data else 0
        else:
            values = [d[variable] for d in data]
            value = sum(values) / len(values) if values else 0
        by_gouvernorat.append({"gouvernorat": gouv, "value": round(value * 100, 1) if variable in ["installation_reussie", "client_satisfait", "client_a_reclame"] else round(value, 1)})
    
    # Correlation factors
    factors = []
    if variable == "installation_reussie":
        factors = [
            {"factor": "Débit réseau", "correlation": 0.72, "impact": "positif"},
            {"factor": "Nombre d'essais", "correlation": -0.85, "impact": "négatif"},
            {"factor": "Durée installation", "correlation": -0.68, "impact": "négatif"},
            {"factor": "Système d'exploitation", "correlation": 0.45, "impact": "positif"},
        ]
    elif variable == "client_satisfait":
        factors = [
            {"factor": "Installation réussie", "correlation": 0.89, "impact": "positif"},
            {"factor": "Réclamations", "correlation": -0.76, "impact": "négatif"},
            {"factor": "Durée installation", "correlation": -0.54, "impact": "négatif"},
            {"factor": "Nombre d'essais", "correlation": -0.62, "impact": "négatif"},
        ]
    elif variable == "client_a_reclame":
        factors = [
            {"factor": "Installation échouée", "correlation": 0.78, "impact": "positif"},
            {"factor": "Durée installation", "correlation": 0.65, "impact": "positif"},
            {"factor": "Nombre d'essais", "correlation": 0.71, "impact": "positif"},
            {"factor": "Débit réseau", "correlation": -0.48, "impact": "négatif"},
        ]
    elif variable == "Duree_installation_minutes":
        factors = [
            {"factor": "Débit réseau", "correlation": -0.82, "impact": "négatif"},
            {"factor": "Taille site", "correlation": 0.56, "impact": "positif"},
            {"factor": "Système d'exploitation", "correlation": 0.38, "impact": "positif"},
            {"factor": "Mode installation", "correlation": 0.22, "impact": "positif"},
        ]
    else:  # nombre_essais_installation
        factors = [
            {"factor": "Débit réseau", "correlation": -0.67, "impact": "négatif"},
            {"factor": "Système d'exploitation", "correlation": 0.52, "impact": "positif"},
            {"factor": "Version produit", "correlation": -0.31, "impact": "négatif"},
            {"factor": "Gouvernorat", "correlation": 0.28, "impact": "positif"},
        ]
    
    return {
        "variable": variable,
        "temporal": temporal_data[-24:],  # Last 24 months
        "by_product": by_product,
        "by_gouvernorat": sorted(by_gouvernorat, key=lambda x: x["value"], reverse=True)[:10],
        "factors": factors
    }

@app.get("/dashboard/predictions")

def get_predictions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["directeur", "admin"]))
):
    from app.services.analytics import predictions as sarima_predictions

    result = sarima_predictions(db)

    return {
        "predictions": result.get("predictions", []),
        "plotly_figures": result.get("plotly_figures", {}),
        "finetuned_models": result.get("finetuned_models", []),
        "message": result.get("message", "SARIMA predictions")
    }
@app.get("/dashboard/risk-analysis")
async def get_risk_analysis(current_user: dict = Depends(require_role(["directeur", "admin"]))):
    # Calculate risk for each installation
    def calc_risk_details(inst):
        score = 0
        factors = []
        
        if inst["Debit_reseau_Mbps"] < 5:
            score += 1
            factors.append("Débit réseau faible")
        if inst["nombre_essais_installation"] > 2:
            score += 1
            factors.append("Nombre d'essais élevé")
        if inst["Duree_installation_minutes"] > 120:
            score += 1
            factors.append("Durée installation longue")
        if inst["Systeme_exploitation_poste"] in ["WindowsXP", "Win7", "Win8"]:
            score += 1
            factors.append("Système d'exploitation ancien")
        if inst["Nom_produit"] == "GRB":
            score += 1
            factors.append("Produit complexe (GRB)")
        if inst["Gouvernorat"] in ["Gafsa", "Jendouba", "Kasserine", "Médenine", "Tataouine"]:
            score += 1
            factors.append("Zone géographique difficile")
        if inst["Taille_site_postes"] > 15:
            score += 1
            factors.append("Site de grande taille")
        
        return score, factors
    
    risk_scores = []
    risk_factors_count = {}
    
    for inst in INSTALLATIONS_DB:
        score, factors = calc_risk_details(inst)
        risk_scores.append(score)
        for f in factors:
            risk_factors_count[f] = risk_factors_count.get(f, 0) + 1
    
    # Score distribution
    score_distribution = {}
    for s in risk_scores:
        score_distribution[s] = score_distribution.get(s, 0) + 1
    
    # Top risk factors
    top_factors = sorted(risk_factors_count.items(), key=lambda x: x[1], reverse=True)
    
    # Clients at risk (score >= 3)
    at_risk = sum(1 for s in risk_scores if s >= 3)
    total = len(risk_scores)
    
    # Recommendations
    recommendations = [
        {"priority": 1, "action": "Améliorer le débit réseau", "impact": "Réduction de 25% des échecs", "effort": "Moyen"},
        {"priority": 2, "action": "Mettre à jour les systèmes d'exploitation obsolètes", "impact": "Réduction de 18% des problèmes", "effort": "Élevé"},
        {"priority": 3, "action": "Planifier les installations hors weekend", "impact": "Amélioration de 12% de la satisfaction", "effort": "Faible"},
        {"priority": 4, "action": "Former les techniciens sur GRB", "impact": "Réduction de 15% du temps d'installation", "effort": "Moyen"},
        {"priority": 5, "action": "Prévoir des interventions anticipées en zones rurales", "impact": "Réduction de 20% des réclamations", "effort": "Moyen"},
    ]
    
    return {
        "taux_risque": round(at_risk / total * 100, 1) if total > 0 else 0,
        "nb_clients_risque": at_risk,
        "total_clients": total,
        "score_distribution": [{"score": k, "count": v} for k, v in sorted(score_distribution.items())],
        "top_factors": [{"factor": f, "count": c, "percentage": round(c / total * 100, 1)} for f, c in top_factors[:7]],
        "recommendations": recommendations
    }

@app.get("/dashboard/installations")
async def get_all_installations(current_user: dict = Depends(require_role(["directeur", "admin"]))):
    return INSTALLATIONS_DB

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CNI Analytics API"}
