"""Request/response DTOs for resume upload and processing status."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    status: str
    failure_reason: str | None = None
    page_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeProcessingStep(BaseModel):
    """One row in the Step 2 "Resume Processing" progress UI."""

    key: str  # "extraction" | "ai_analysis" | "portfolio_generation" | "website_generation"
    label: str
    status: str  # "pending" | "in_progress" | "complete" | "failed"
    detail: str | None = None


class ResumeProcessingStatus(BaseModel):
    resume_id: str
    overall_status: str
    steps: list[ResumeProcessingStep]
    portfolio_id: str | None = None
