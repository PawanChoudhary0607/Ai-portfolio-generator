"""SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Used for local dev / first run.

    In production this is replaced by Alembic migrations (see
    backend/alembic/) so schema changes are versioned and reviewable
    instead of inferred from model state.
    """
    from app.database import models  # noqa: F401  (registers models on Base)

    Base.metadata.create_all(bind=engine)
