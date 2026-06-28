"""AI analysis package — public API."""

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.analyzer import analyze, analyze_and_save
from src.ai.exceptions import (
    AIError,
    MalformedResponseError,
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
    SchemaValidationError,
)

__all__ = [
    "analyze",
    "analyze_and_save",
    "AIAnalysisSchema",
    "AIError",
    "OllamaUnavailableError",
    "ModelNotFoundError",
    "OllamaTimeoutError",
    "MalformedResponseError",
    "SchemaValidationError",
]
