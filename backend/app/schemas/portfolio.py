"""Request/response DTOs for portfolio listing, detail, theme, preview, and export endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, model_validator


class PortfolioOut(BaseModel):
    id: str
    resume_id: str
    title: str
    status: str
    failure_reason: str | None = None
    selected_theme: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioDetailOut(PortfolioOut):
    portfolio_schema_json: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _strip_internal_fields(self) -> "PortfolioDetailOut":
        # `llm_model` records which Ollama model generated this content.
        # That's internal configuration, not user-facing portfolio data —
        # never let it leave the backend (see generator_service docstring
        # for the same rule applied to error messages).
        if self.portfolio_schema_json is not None:
            self.portfolio_schema_json = {
                k: v for k, v in self.portfolio_schema_json.items() if k != "llm_model"
            }
        return self


class ThemeOut(BaseModel):
    """One entry in the static theme catalog (Step 3 — Theme Selection)."""

    value: str
    label: str
    description: str

