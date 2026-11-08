import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")


def _is_render_deployment() -> bool:
    return any(
        os.getenv(flag)
        for flag in ("RENDER", "RENDER_SERVICE_ID", "RENDER_EXTERNAL_URL")
    )


def _resolve_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    if _is_render_deployment():
        raise RuntimeError(
            "DATABASE_URL is not configured in the Render service environment. "
            "Set the backend service variable or attach the Render PostgreSQL resource."
        )

    return "postgresql+psycopg://postgres:ayoubdb@localhost:5432/bd_installations_CNI"


@dataclass(frozen=True)
class Settings:
    app_name: str = "SADP API"
    app_version: str = "2.0.0"
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    database_url: str = field(default_factory=_resolve_database_url)
    cors_origins: list[str] = field(
        default_factory=lambda: [s.strip() for s in os.getenv("CORS_ORIGINS", "*").split(",")]
    )


settings = Settings()
