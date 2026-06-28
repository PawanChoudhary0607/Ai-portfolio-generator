"""Custom exceptions for the AI analysis module."""

from __future__ import annotations


class AIError(Exception):
    """Base class for all AI layer failures."""


class OllamaUnavailableError(AIError):
    """Raised when the Ollama server cannot be reached."""

    def __init__(self, url: str, original_error: Exception | None = None) -> None:
        self.url = url
        self.original_error = original_error
        super().__init__(f"Ollama server unavailable at '{url}'")


class ModelNotFoundError(AIError):
    """Raised when the requested model is not available in Ollama."""

    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"Model not found in Ollama: '{model}'")


class OllamaTimeoutError(AIError):
    """Raised when the Ollama request exceeds the configured timeout."""

    def __init__(self, model: str, timeout: int) -> None:
        self.model = model
        self.timeout = timeout
        super().__init__(f"Ollama request timed out after {timeout}s for model '{model}'")


class MalformedResponseError(AIError):
    """Raised when the model response cannot be parsed as valid JSON."""

    def __init__(self, reason: str, raw_response: str = "") -> None:
        self.reason = reason
        self.raw_response = raw_response
        super().__init__(f"Malformed model response: {reason}")


class SchemaValidationError(AIError):
    """Raised when parsed JSON does not conform to AIAnalysisSchema."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"AI output schema validation failed: {reason}")
