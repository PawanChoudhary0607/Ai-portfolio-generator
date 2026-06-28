"""Custom exceptions for the portfolio generation module."""

from __future__ import annotations


class PortfolioError(Exception):
    """Base class for all portfolio generation failures."""


class PortfolioGenerationError(PortfolioError):
    """Raised when the LLM call for portfolio generation fails or returns unusable output."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Portfolio generation failed: {reason}")


class PortfolioValidationError(PortfolioError):
    """Raised when the assembled PortfolioSchema fails field-level validation."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Portfolio validation failed — field '{field}': {reason}")
