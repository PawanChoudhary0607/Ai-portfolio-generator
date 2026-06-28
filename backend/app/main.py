"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.database.session import init_db

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "Backend for the AI Portfolio Generator SaaS. Wraps the frozen "
        "website-generator/ engine behind a REST API — see "
        "app/services/generator_service.py for the isolation boundary."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup() -> None:
    # Local development uses create_all for convenience.
    # Once the schema stabilizes, switch to `alembic upgrade head` here
    # (or in a deploy step) instead — see backend/alembic/.
    init_db()


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}

