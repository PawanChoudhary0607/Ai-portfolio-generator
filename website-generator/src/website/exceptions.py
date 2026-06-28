"""Custom exceptions for the website generation module."""

from __future__ import annotations


class WebsiteError(Exception):
    """Base class for all website generation failures."""


class WebsiteGenerationError(WebsiteError):
    """Raised when website generation fails (missing template, write error, etc.)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Website generation failed: {reason}")
