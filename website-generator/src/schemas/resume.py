"""Pydantic v2 schema for a parsed resume.

All fields are optional — real-world resumes are inconsistent.
raw_text is always preserved for downstream LLM use.
Deep field parsing (dates, structured experience) is deferred to the LLM milestone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "2.0"
PARSER_VERSION = "1.0"


class PersonalInfo(BaseModel):
    """Contact and identity fields."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None


class ResumeSchema(BaseModel):
    """Top-level schema for an extracted and lightly parsed resume.

    Sections (experience, education, projects) are stored as raw text blocks.
    Structured parsing of those blocks is deferred to the LLM milestone.
    """

    # ── Metadata ────────────────────────────────────────────────────────────
    schema_version: str = Field(default=SCHEMA_VERSION)
    parser_version: str = Field(default=PARSER_VERSION)
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ── Source ──────────────────────────────────────────────────────────────
    filename: Optional[str] = None
    page_count: Optional[int] = None
    raw_text: Optional[str] = None

    # ── Parsed fields ───────────────────────────────────────────────────────
    personal: Optional[PersonalInfo] = None
    summary: Optional[str] = None

    # Canonical capitalisation preserved — "Python", "AWS", "React", not lowercased
    skills: list[str] = Field(default_factory=list)

    # Raw section text — not structured until LLM milestone
    experience_raw: Optional[str] = None
    education_raw: Optional[str] = None
    projects_raw: Optional[str] = None
    certifications_raw: Optional[str] = None
