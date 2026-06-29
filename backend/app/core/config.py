"""Application configuration.

All settings are loaded from environment variables (with sane local-dev
defaults) so the same codebase runs unchanged in dev, CI, and production.
Never hardcode secrets here — see .env.example for the variables this
file expects.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Portfolio Generator API"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-portfolio-generator-smoky.vercel.app",
    ]

    # ── Database ─────────────────────────────────────────────────────
    # SQLite for local development. Swap for a Postgres DSN in production
    # (e.g. postgresql+psycopg://user:pass@host:5432/portfolio_saas) —
    # nothing else in the codebase needs to change.
    DATABASE_URL: str = f"sqlite:///{BACKEND_ROOT / 'data' / 'app.db'}"

    # ── Auth / JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-only-secret-change-me-before-deploying"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_BCRYPT_ROUNDS: int = 10

    # ── Storage ──────────────────────────────────────────────────────
    STORAGE_DIR: Path = BACKEND_ROOT / "storage"
    RESUME_STORAGE_DIR: Path = BACKEND_ROOT / "storage" / "resumes"
    EXPORT_STORAGE_DIR: Path = BACKEND_ROOT / "storage" / "exports"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_UPLOAD_CONTENT_TYPES: tuple[str, ...] = ("application/pdf",)

    # ── Generator engine (website-generator/) ───────────────────────
    GENERATOR_ROOT: Path = REPO_ROOT / "website-generator"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:14b"
    OLLAMA_TIMEOUT_SECONDS: int = 120


settings = Settings()

# Ensure local dev directories exist on import.
(BACKEND_ROOT / "data").mkdir(parents=True, exist_ok=True)
settings.RESUME_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
