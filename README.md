# SADP Decision Support System

Application web full-stack pour la supervision des installations des produits CNI et l'aide a la decision analytique.

## 1. Stack technique

- Frontend: Next.js (React + TypeScript)
- Backend: FastAPI (Python)
- Base de donnees: PostgreSQL
- ORM: SQLAlchemy
- Auth: JWT
- Graphiques: Plotly (backend + frontend)

## 2. Prerequis

Installe ces outils avant de commencer:

- Python 3.12+
- Node.js 20+
- pnpm 10+
- PostgreSQL (local)

Verification rapide:

```powershell
python --version
node --version
pnpm --version
```

## 3. Structure du projet

- backend: API FastAPI + SQLAlchemy + seed demo
- frontend: interface SaaS enterprise

## 4. Configuration depuis zero

### 4.1 Cloner et ouvrir

```powershell
git clone <URL_DU_REPO>
cd siteCNI3
```

### 4.2 Configurer PostgreSQL local

Assure-toi que PostgreSQL tourne en local avec:

- host: localhost
- port: 5432
- user: postgres
- password: malak
- database: bd_installations_CNI

Si la base n'existe pas:

```sql
CREATE DATABASE bd_installations_CNI;
```

### 4.3 Configurer le backend

Le fichier backend/.env doit contenir:

```env
DATABASE_URL=postgresql+psycopg://postgres:malak@localhost:5432/bd_installations_CNI
OR
DATABASE_URL=postgresql+psycopg://postgres:ayoubdb@localhost:5432/bd_installations_CNI
JWT_SECRET=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3000
```

Installer les dependances backend:

```powershell
cd backend
pip install -e .
```

Lancer le backend:

```powershell
uvicorn main:app --reload --port 8000
```

API disponible sur:

- http://localhost:8000
- http://localhost:8000/docs
- http://localhost:8000/health

### 4.4 Configurer le frontend

Dans un deuxieme terminal:

```powershell
cd frontend
pnpm install
```

Le fichier frontend/.env.local doit contenir:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Lancer le frontend:

```powershell
pnpm dev
```

Frontend disponible sur:

- http://localhost:3000

## 5. Comptes demo

Utilise les comptes suivants sur la page login:

- Client: client@demo.com / demo123
- Admin: admin@demo.com / demo123
- Directeur: directeur@demo.com / demo123

## 6. Endpoints principaux

### Auth

- POST /login
- GET /me

### Client

- GET /products
- POST /update-product
- POST /products/{product_id}/update
- GET /notifications
- GET /client/installations

### Admin

- GET /admin/users
- POST /admin/users
- PUT /admin/users/{user_id}
- DELETE /admin/users/{user_id}
- GET /admin/products
- POST /admin/products
- PUT /admin/products/{product_id}
- DELETE /admin/products/{product_id}
- PUT /permissions

### Dashboard

- GET /dashboard/kpis
- GET /dashboard/target/{variable}
- GET /dashboard/predictions
- GET /dashboard/risk-analysis

## 7. Integration analyse_copy.py

Le backend tente d'importer automatiquement analyse_copy.py s'il existe dans l'un de ces chemins:

- backend/analyse_copy.py
- analyse_copy.py (racine du workspace)

Si le fichier n'existe pas, l'application utilise les services analytiques internes (fallback).

## 8. Premier lancement: checklist rapide

1. Verifier PostgreSQL local actif
2. Lancer backend (port 8000)
3. Lancer frontend (port 3000)
4. Ouvrir http://localhost:3000
5. Se connecter avec un compte demo

## 9. Depannage

### Erreur connexion DB

- Verifier user/password/base dans backend/.env
- Verifier que PostgreSQL ecoute bien sur localhost:5432

### CORS ou API inaccessible

- Verifier CORS_ORIGINS dans backend/.env
- Verifier NEXT_PUBLIC_API_URL dans frontend/.env.local

### Port deja utilise

- Changer le port backend:

```powershell
uvicorn main:app --reload --port 8001
```

et adapter frontend/.env.local:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 10. Commandes resume

Terminal 1 (backend):

```powershell
cd backend
pip install -e .
uvicorn main:app --reload --port 8000
```

Terminal 2 (frontend):

```powershell
cd frontend
pnpm install
pnpm dev
```
