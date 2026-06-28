"""Orchestrates the upload-to-website pipeline and exposes a status snapshot the frontend can poll while it runs.

Concurrency note: pipeline steps run via FastAPI BackgroundTasks, which executes in-process after the response is sent. That is fine for local dev and demos, but each AI call can be slow and ties up the request worker. For higher traffic, move run_pipeline to a task queue so uploads scale independently of the API process.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Portfolio, PortfolioStatus, Resume, ResumeStatus, ThemeName
from app.database.session import SessionLocal
from app.services import generator_service

logger = logging.getLogger(__name__)

# Step keys/labels shared between the pipeline and the status DTO so the
# frontend always renders rows in a stable, known order.
PIPELINE_STEPS: list[tuple[str, str]] = [
    ("extraction", "Extracting text from PDF"),
    ("ai_analysis", "Analyzing resume with AI"),
    ("portfolio_generation", "Generating portfolio content"),
    ("website_generation", "Preparing website data"),
]


def create_resume_record(
    db: Session, *, user_id: str, original_filename: str, storage_path: Path, file_size_bytes: int
) -> Resume:
    resume = Resume(
        user_id=user_id,
        original_filename=original_filename,
        storage_path=str(storage_path),
        file_size_bytes=file_size_bytes,
        status=ResumeStatus.UPLOADED,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def run_pipeline(resume_id: str) -> None:
    """Runs the full pipeline for one resume. Designed to be handed to
    FastAPI's BackgroundTasks, so it opens its own DB session rather than
    reusing the request-scoped one (which closes as soon as the response
    is returned).
    """
    db = SessionLocal()
    try:
        resume = db.get(Resume, resume_id)
        if resume is None:
            logger.error("run_pipeline: resume %s not found", resume_id)
            return

        try:
            _run_extraction(db, resume)
            _run_analysis(db, resume)
            portfolio = _run_portfolio_generation(db, resume)
            _run_website_generation(db, portfolio)
        except generator_service.GeneratorServiceError as exc:
            logger.warning("Pipeline failed for resume %s at stage '%s': %s", resume_id, exc.stage, exc)
            _mark_failed(db, resume, stage=exc.stage, reason=str(exc))
    finally:
        db.close()


def _run_extraction(db: Session, resume: Resume) -> None:
    resume.status = ResumeStatus.EXTRACTING
    db.commit()

    page_count, raw_text = generator_service.extract_resume_text(Path(resume.storage_path))
    resume_schema_dict = generator_service.parse_resume(
        raw_text, filename=resume.original_filename, page_count=page_count
    )

    resume.page_count = page_count
    resume.resume_schema_json = resume_schema_dict
    resume.status = ResumeStatus.EXTRACTED
    db.commit()


def _run_analysis(db: Session, resume: Resume) -> None:
    resume.status = ResumeStatus.ANALYZING
    db.commit()

    analysis_dict = generator_service.analyze_resume(resume.resume_schema_json)

    resume.ai_analysis_json = analysis_dict
    resume.status = ResumeStatus.ANALYZED
    db.commit()


def _run_portfolio_generation(db: Session, resume: Resume) -> Portfolio:
    portfolio = Portfolio(
        user_id=resume.user_id,
        resume_id=resume.id,
        status=PortfolioStatus.GENERATING,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    portfolio_dict = generator_service.generate_portfolio(
        resume.resume_schema_json, resume.ai_analysis_json
    )

    hero = portfolio_dict.get("hero") or {}
    name = hero.get("name") or "Untitled"

    portfolio.portfolio_schema_json = portfolio_dict
    portfolio.title = f"{name}'s portfolio"
    portfolio.status = PortfolioStatus.DRAFT
    db.commit()
    db.refresh(portfolio)
    return portfolio


def _run_website_generation(db: Session, portfolio: Portfolio) -> None:
    default_theme = generator_service.THEME_CATALOG[0]["value"]
    export_dir = settings.EXPORT_STORAGE_DIR / portfolio.id / default_theme
    generator_service.render_theme_to_directory(
        portfolio.portfolio_schema_json, default_theme, export_dir
    )
    portfolio.selected_theme = ThemeName(default_theme)
    db.commit()


def _mark_failed(db: Session, resume: Resume, *, stage: str, reason: str) -> None:
    if stage in ("extraction", "ai_analysis"):
        resume.status = ResumeStatus.FAILED
        resume.failure_reason = reason
        resume.failed_stage = stage
        db.commit()
        return

    # Failure happened after a Portfolio row was created.
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.resume_id == resume.id)
        .order_by(Portfolio.created_at.desc())
        .first()
    )
    if portfolio is not None:
        portfolio.status = PortfolioStatus.FAILED
        portfolio.failure_reason = reason
        db.commit()
    else:
        resume.status = ResumeStatus.FAILED
        resume.failure_reason = reason
        db.commit()


def get_processing_status(db: Session, resume: Resume) -> dict:
    """Builds the Step-2 progress payload from current DB state."""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.resume_id == resume.id)
        .order_by(Portfolio.created_at.desc())
        .first()
    )

    step_status: dict[str, str] = {key: "pending" for key, _ in PIPELINE_STEPS}
    detail: dict[str, str | None] = {key: None for key, _ in PIPELINE_STEPS}

    if resume.status == ResumeStatus.FAILED:
        failed_key = resume.failed_stage or "extraction"
        for key in step_status:
            if key == failed_key:
                step_status[key] = "failed"
                detail[key] = resume.failure_reason
                break
            step_status[key] = "complete"
        return _build_status_payload(resume, step_status, detail, "failed", None)

    if resume.status == ResumeStatus.EXTRACTING:
        step_status["extraction"] = "in_progress"
    elif resume.status in (
        ResumeStatus.EXTRACTED,
        ResumeStatus.ANALYZING,
        ResumeStatus.ANALYZED,
    ):
        step_status["extraction"] = "complete"
        if resume.status == ResumeStatus.ANALYZING:
            step_status["ai_analysis"] = "in_progress"
        elif resume.status == ResumeStatus.ANALYZED:
            step_status["ai_analysis"] = "complete"

    if portfolio is not None:
        step_status["extraction"] = "complete"
        step_status["ai_analysis"] = "complete"
        if portfolio.status == PortfolioStatus.GENERATING:
            step_status["portfolio_generation"] = "in_progress"
        elif portfolio.status == PortfolioStatus.DRAFT:
            step_status["portfolio_generation"] = "complete"
            step_status["website_generation"] = "complete"
        elif portfolio.status == PortfolioStatus.FAILED:
            step_status["portfolio_generation"] = "failed"
            detail["portfolio_generation"] = portfolio.failure_reason

    if all(v == "complete" for v in step_status.values()):
        overall = "complete"
    elif any(v == "failed" for v in step_status.values()):
        overall = "failed"
    else:
        overall = "in_progress"

    return _build_status_payload(resume, step_status, detail, overall, portfolio.id if portfolio else None)


def _build_status_payload(
    resume: Resume,
    step_status: dict[str, str],
    detail: dict[str, str | None],
    overall: str,
    portfolio_id: str | None,
) -> dict:
    return {
        "resume_id": resume.id,
        "overall_status": overall,
        "portfolio_id": portfolio_id,
        "steps": [
            {"key": key, "label": label, "status": step_status[key], "detail": detail[key]}
            for key, label in PIPELINE_STEPS
        ],
    }

