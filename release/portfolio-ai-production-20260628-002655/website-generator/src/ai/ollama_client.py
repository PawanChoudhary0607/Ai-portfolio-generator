"""Ollama client — the only module allowed to communicate with Ollama.

All other modules call this client. No other module imports ollama directly.
"""

from __future__ import annotations

import logging

import ollama
from ollama import ResponseError

from src.ai.exceptions import (
    MalformedResponseError,
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_TIMEOUT = 120  # seconds


class OllamaClient:
    """Thin wrapper around the Ollama Python client.

    Responsibilities:
    - Send prompts to a local Ollama server.
    - Handle all network, timeout, and model errors.
    - Return raw response text only — no parsing happens here.
    """

    def __init__(
        self,
        model: str,
        host: str = DEFAULT_HOST,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.model = model
        self.host = host
        self.timeout = timeout
        self._client = ollama.Client(host=host)

    def generate(self, prompt: str) -> str:
        """Send prompt to Ollama and return the raw response string.

        Raises:
            OllamaUnavailableError: server not reachable.
            ModelNotFoundError: model not pulled in Ollama.
            OllamaTimeoutError: request exceeded timeout.
            MalformedResponseError: response structure is unexpected.
        """
        logger.info("Sending prompt to model '%s' at '%s'", self.model, self.host)

        try:
            response = self._client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.1},
                stream=False,
            )
        except ResponseError as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                raise ModelNotFoundError(self.model) from e
            raise OllamaUnavailableError(self.host, original_error=e) from e
        except TimeoutError as e:
            raise OllamaTimeoutError(self.model, self.timeout) from e
        except ConnectionError as e:
            raise OllamaUnavailableError(self.host, original_error=e) from e
        except Exception as e:
            # Catch socket-level and httpx errors by message content
            error_str = str(e).lower()
            if "connection" in error_str or "connect" in error_str:
                raise OllamaUnavailableError(self.host, original_error=e) from e
            if "timed out" in error_str or "timeout" in error_str:
                raise OllamaTimeoutError(self.model, self.timeout) from e
            raise OllamaUnavailableError(self.host, original_error=e) from e

        try:
            text = response["response"]
        except (KeyError, TypeError) as e:
            raise MalformedResponseError(
                "response dict missing 'response' key", raw_response=str(response)
            ) from e

        if not isinstance(text, str) or not text.strip():
            raise MalformedResponseError(
                "response text is empty", raw_response=str(response)
            )

        logger.info("Received response (%d chars)", len(text))
        return text
