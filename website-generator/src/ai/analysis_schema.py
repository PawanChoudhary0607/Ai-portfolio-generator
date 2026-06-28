"""Pydantic v2 schema for AI-generated resume analysis.

This schema is the contract between Milestone 3 and all future milestones.
All fields are required — the AI layer must always produce a complete analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

ANALYSIS_SCHEMA_VERSION = "3.0"


class AIAnalysisSchema(BaseModel):
    """Structured output from the local LLM resume analysis pipeline.

    Never instantiated with raw model output — always constructed via
    validators.parse_and_validate() which enforces schema correctness.
    """

    # ── Metadata ─────────────────────────────────────────────────────────────
    schema_version: str = Field(default=ANALYSIS_SCHEMA_VERSION)
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    llm_model: str = Field(default="")

    # ── Analysis fields (all required) ───────────────────────────────────────
    strengths: list[str]
    weaknesses: list[str]
    missing_skills: list[str]
    recommended_projects: list[str]
    recommended_career_paths: list[str]
    portfolio_sections: list[str]
    summary: str
