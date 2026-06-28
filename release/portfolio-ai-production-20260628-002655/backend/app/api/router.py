"""Aggregates every route module under a single APIRouter mounted by main.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, dashboard, portfolios, resumes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(resumes.router)
api_router.include_router(portfolios.router)
