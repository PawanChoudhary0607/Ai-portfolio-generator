"""Portfolio routes for listing, theme rendering, website preview, and export."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.models import Portfolio, PortfolioStatus, ThemeName, User
from app.database.session import get_db
from app.schemas.portfolio import PortfolioDetailOut, PortfolioOut, ThemeOut
from app.services import generator_service
from app.services.generator_service import THEME_CATALOG

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


class ThemeRequest(BaseModel):
    theme: str


@router.get("/themes/catalog", response_model=list[ThemeOut])
def list_theme_catalog() -> list[ThemeOut]:
    return [ThemeOut.model_validate(t) for t in THEME_CATALOG]


@router.get("/themes/{theme}/demo-website", response_class=HTMLResponse)
def demo_theme_website(theme: str) -> HTMLResponse:
    _validate_theme(theme)
    fixture = settings.GENERATOR_ROOT / "tests" / "website" / "fixtures" / "valid_portfolio.json"
    try:
        import json

        portfolio_dict = json.loads(fixture.read_text(encoding="utf-8"))
        files = generator_service.render_theme_preview(portfolio_dict, theme)
    except (OSError, generator_service.GeneratorServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't prepare this theme preview. Please try again.",
        ) from exc
    return HTMLResponse(_inline_css(files))


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[PortfolioOut]:
    portfolios = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.updated_at.desc())
        .all()
    )
    return [PortfolioOut.model_validate(p) for p in portfolios]


@router.get("/{portfolio_id}", response_model=PortfolioDetailOut)
def get_portfolio(
    portfolio_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> PortfolioDetailOut:
    portfolio = _get_owned_portfolio_or_404(db, portfolio_id, current_user.id)
    return PortfolioDetailOut.model_validate(portfolio)


@router.post("/{portfolio_id}/theme-preview")
def generate_theme_preview(
    portfolio_id: str,
    payload: ThemeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    portfolio = _get_ready_portfolio(db, portfolio_id, current_user.id)
    files = _render_files(portfolio, payload.theme)
    portfolio.selected_theme = ThemeName(payload.theme)
    db.commit()
    return {"html": _inline_css(files), "theme": payload.theme}


@router.get("/{portfolio_id}/website", response_class=HTMLResponse)
def open_website(
    portfolio_id: str,
    theme: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    portfolio = _get_ready_portfolio(db, portfolio_id, current_user.id)
    theme_value = theme or _selected_theme(portfolio)
    files = _render_files(portfolio, theme_value)
    return HTMLResponse(_inline_css(files))


@router.get("/{portfolio_id}/export/html")
def export_html(
    portfolio_id: str,
    theme: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    portfolio = _get_ready_portfolio(db, portfolio_id, current_user.id)
    theme_value = theme or _selected_theme(portfolio)
    files = _render_files(portfolio, theme_value)
    filename = _download_stem(portfolio, theme_value) + ".html"
    return HTMLResponse(
        _inline_css(files),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{portfolio_id}/export/zip")
def export_zip(
    portfolio_id: str,
    theme: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    portfolio = _get_ready_portfolio(db, portfolio_id, current_user.id)
    theme_value = theme or _selected_theme(portfolio)
    export_dir = _ensure_export_dir(portfolio, theme_value)
    zip_path = export_dir.with_suffix(".zip")

    try:
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in export_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(export_dir))
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't package your website. Please try again.",
        ) from exc

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=_download_stem(portfolio, theme_value) + ".zip",
    )


def _get_owned_portfolio_or_404(db: Session, portfolio_id: str, user_id: str) -> Portfolio:
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


def _get_ready_portfolio(db: Session, portfolio_id: str, user_id: str) -> Portfolio:
    portfolio = _get_owned_portfolio_or_404(db, portfolio_id, user_id)
    if not portfolio.portfolio_schema_json or portfolio.status == PortfolioStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This portfolio is not ready yet. Please wait for generation to finish.",
        )
    return portfolio


def _validate_theme(theme: str) -> None:
    if theme not in generator_service.VALID_THEME_VALUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown theme")


def _selected_theme(portfolio: Portfolio) -> str:
    if portfolio.selected_theme:
        return portfolio.selected_theme.value
    return THEME_CATALOG[0]["value"]


def _render_files(portfolio: Portfolio, theme: str) -> dict[str, str]:
    _validate_theme(theme)
    try:
        return generator_service.render_theme_preview(portfolio.portfolio_schema_json, theme)
    except generator_service.GeneratorServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


def _ensure_export_dir(portfolio: Portfolio, theme: str) -> Path:
    _validate_theme(theme)
    export_dir = settings.EXPORT_STORAGE_DIR / portfolio.id / theme
    try:
        if export_dir.exists():
            shutil.rmtree(export_dir)
        generator_service.render_theme_to_directory(portfolio.portfolio_schema_json, theme, export_dir)
    except (OSError, generator_service.GeneratorServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't prepare your website export. Please try again.",
        ) from exc
    return export_dir


def _inline_css(files: dict[str, str]) -> str:
    html = files["index.html"]
    css = files.get("styles.css", "")
    return html.replace('<link rel="stylesheet" href="styles.css" />', f"<style>\n{css}\n</style>")


def _download_stem(portfolio: Portfolio, theme: str) -> str:
    title = "".join(ch.lower() if ch.isalnum() else "-" for ch in portfolio.title).strip("-")
    while "--" in title:
        title = title.replace("--", "-")
    return f"{title or 'portfolio'}-{theme}"
