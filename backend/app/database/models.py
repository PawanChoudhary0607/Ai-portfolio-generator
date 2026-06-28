"""Database models for users, resumes, generated portfolios, exports, and versioned publishing records."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ──────────────────────────────────────────────────────────────────


class ResumeStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class PortfolioStatus(str, enum.Enum):
    GENERATING = "generating"
    DRAFT = "draft"
    PUBLISHED = "published"
    FAILED = "failed"


class ThemeName(str, enum.Enum):
    MINIMAL = "minimal-white-orange"
    EXECUTIVE = "executive-black-gold"
    DEVELOPER = "developer-dark"
    CREATIVE = "creative-portfolio"
    SAAS = "modern-saas"


class DeploymentProvider(str, enum.Enum):
    NONE = "none"
    NETLIFY = "netlify"
    VERCEL = "vercel"
    S3 = "s3"


class DeploymentState(str, enum.Enum):
    NOT_DEPLOYED = "not_deployed"
    QUEUED = "queued"
    DEPLOYING = "deploying"
    LIVE = "live"
    FAILED = "failed"


# ── Users ────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PasswordResetToken(Base):
    """A short-lived, single-use token issued for the Forgot Password flow.

    The token value emailed to the user is never stored — only its hash
    (see core/security.py:hash_reset_token) — so a database leak alone
    cannot be used to reset an account.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="reset_tokens")


# ── Resumes ──────────────────────────────────────────────────────────────


class Resume(Base):
    """One uploaded PDF and the artifacts produced by the extraction/AI
    pipeline (engine calls live in services/generator_service.py).
    """

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus), default=ResumeStatus.UPLOADED, nullable=False
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resume_schema_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="resumes")
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


# ── Portfolio data ───────────────────────────────────────────────────────


class Portfolio(Base):
    """The generated PortfolioSchema for one resume, plus its publishing
    state. A resume can in principle produce more than one Portfolio row
    over time (regenerated after editing the source resume), but the
    common case is a 1:1 relationship.
    """

    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled portfolio")
    status: Mapped[PortfolioStatus] = mapped_column(
        Enum(PortfolioStatus), default=PortfolioStatus.GENERATING, nullable=False
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio_schema_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    selected_theme: Mapped[ThemeName | None] = mapped_column(Enum(ThemeName), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    resume: Mapped["Resume"] = relationship(back_populates="portfolios")
    drafts: Mapped[list["Draft"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    theme_selections: Mapped[list["ThemeSelection"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    published_sites: Mapped[list["PublishedSite"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    versions: Mapped[list["VersionHistory"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class ThemeSelection(Base):
    """Records which theme previews have been generated/considered for a
    portfolio and which one is currently active. Kept separate from
    Portfolio.selected_theme (the live pointer) so the editor can show
    "you previewed 3 of 5 themes" and let the user flip back without
    regenerating.
    """

    __tablename__ = "theme_selections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), nullable=False, index=True)
    theme: Mapped[ThemeName] = mapped_column(Enum(ThemeName), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preview_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="theme_selections")


class Draft(Base):
    """An autosaved, unpublished snapshot of edits made in the visual
    editor. Distinct from VersionHistory: drafts are mutable working
    state, versions are immutable checkpoints (e.g. taken on publish).
    """

    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), nullable=False, index=True)
    data_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="drafts")


# ── Publishing ───────────────────────────────────────────────────────────


class PublishedSite(Base):
    """A live (or previously live) published portfolio. slug is the
    public path segment, e.g. /p/<slug>.
    """

    __tablename__ = "published_sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    theme: Mapped[ThemeName] = mapped_column(Enum(ThemeName), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="published_sites")
    deployment: Mapped["DeploymentStatus | None"] = relationship(
        back_populates="published_site", cascade="all, delete-orphan", uselist=False
    )


class DeploymentStatus(Base):
    """One-click deploy status for a published site.
    Modeled now so PublishedSite doesn't need a schema migration later.
    """

    __tablename__ = "deployment_statuses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    published_site_id: Mapped[str] = mapped_column(
        ForeignKey("published_sites.id"), nullable=False, unique=True, index=True
    )
    provider: Mapped[DeploymentProvider] = mapped_column(
        Enum(DeploymentProvider), default=DeploymentProvider.NONE, nullable=False
    )
    state: Mapped[DeploymentState] = mapped_column(
        Enum(DeploymentState), default=DeploymentState.NOT_DEPLOYED, nullable=False
    )
    deployed_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    published_site: Mapped["PublishedSite"] = relationship(back_populates="deployment")


class VersionHistory(Base):
    """Immutable snapshot of a portfolio's data + theme at a point in
    time (e.g. taken whenever a portfolio is published).
    """

    __tablename__ = "version_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    theme: Mapped[ThemeName] = mapped_column(Enum(ThemeName), nullable=False)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="versions")

