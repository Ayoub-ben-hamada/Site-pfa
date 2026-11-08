import fastapi
import fastapi.middleware.cors

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from sqlalchemy.exc import OperationalError
from app.routers import admin, auth, client, dashboard, ml_predictions
from app.services.seed import seed_demo_data


app = fastapi.FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_demo_data(db)
        print("Application started. SARIMA models will be trained on first /predictions call.")
    except OperationalError as e:
        # In development, avoid crashing the whole app if the DB isn't available.
        # Log the error and continue; routes that need the DB will fail later.
        print("Database unavailable during startup:", e)


app.include_router(auth.router)
app.include_router(client.router)
app.include_router(admin.router)
app.include_router(admin.permissions_router)
app.include_router(dashboard.router)
app.include_router(ml_predictions.router)


@app.get("/")
def root() -> dict:
    return {"message": "Backend is working"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}
