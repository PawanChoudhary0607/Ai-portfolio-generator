"""Dashboard overview route — backs the five summary panels plus the
"Create New Portfolio" entry point.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import (
    Draft,
    Portfolio,
    PortfolioStatus,
    PublishedSite,
    Resume,
    User,
    VersionHistory,
)
from app.database.session import get_db
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardPortfolioSummary,
    DashboardPublishedSiteSummary,
    DashboardResumeSummary,
    DashboardVersionSummary,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_RECENT_LIMIT = 10


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardOverview:
    recent_resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .limit(_RECENT_LIMIT)
        .all()
    )

    all_portfolios = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.updated_at.desc())
        .limit(_RECENT_LIMIT)
        .all()
    )
    drafts = [p for p in all_portfolios if p.status == PortfolioStatus.DRAFT]

    published_sites = (
        db.query(PublishedSite)
        .join(Portfolio, PublishedSite.portfolio_id == Portfolio.id)
        .filter(Portfolio.user_id == current_user.id)
        .order_by(PublishedSite.published_at.desc())
        .limit(_RECENT_LIMIT)
        .all()
    )

    versions = (
        db.query(VersionHistory)
        .join(Portfolio, VersionHistory.portfolio_id == Portfolio.id)
        .filter(Portfolio.user_id == current_user.id)
        .order_by(VersionHistory.created_at.desc())
        .limit(_RECENT_LIMIT)
        .all()
    )

    return DashboardOverview(
        recent_resumes=[
            DashboardResumeSummary(
                id=r.id, original_filename=r.original_filename, status=r.status.value,
                created_at=r.created_at,
            )
            for r in recent_resumes
        ],
        generated_portfolios=[
            DashboardPortfolioSummary(
                id=p.id, title=p.title, status=p.status.value,
                selected_theme=p.selected_theme.value if p.selected_theme else None,
                updated_at=p.updated_at,
            )
            for p in all_portfolios
        ],
        published_sites=[
            DashboardPublishedSiteSummary(
                id=s.id, portfolio_id=s.portfolio_id, slug=s.slug, is_active=s.is_active,
                published_at=s.published_at,
            )
            for s in published_sites
        ],
        drafts=[
            DashboardPortfolioSummary(
                id=p.id, title=p.title, status=p.status.value,
                selected_theme=p.selected_theme.value if p.selected_theme else None,
                updated_at=p.updated_at,
            )
            for p in drafts
        ],
        version_history=[
            DashboardVersionSummary(
                id=v.id, portfolio_id=v.portfolio_id, version_number=v.version_number,
                created_at=v.created_at,
            )
            for v in versions
        ],
    )
