"""Request/response DTOs for the dashboard overview endpoint."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardResumeSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    created_at: datetime


class DashboardPortfolioSummary(BaseModel):
    id: str
    title: str
    status: str
    selected_theme: str | None = None
    updated_at: datetime


class DashboardPublishedSiteSummary(BaseModel):
    id: str
    portfolio_id: str
    slug: str
    is_active: bool
    published_at: datetime


class DashboardVersionSummary(BaseModel):
    id: str
    portfolio_id: str
    version_number: int
    created_at: datetime


class DashboardOverview(BaseModel):
    recent_resumes: list[DashboardResumeSummary]
    generated_portfolios: list[DashboardPortfolioSummary]
    published_sites: list[DashboardPublishedSiteSummary]
    drafts: list[DashboardPortfolioSummary]
    version_history: list[DashboardVersionSummary]
