"""Unit tests for src/ai/ollama_client.py.

All Ollama network calls are mocked — no real server required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ai.exceptions import (
    MalformedResponseError,
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)
from src.ai.ollama_client import OllamaClient


def _make_client(model: str = "qwen3:8b") -> OllamaClient:
    with patch("src.ai.ollama_client.ollama.Client"):
        return OllamaClient(model=model)


# ── Happy path ────────────────────────────────────────────────────────────────

def test_generate_returns_text():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"response": '{"key": "value"}'})
    result = client.generate("test prompt")
    assert result == '{"key": "value"}'


def test_generate_calls_ollama_with_correct_model():
    client = _make_client(model="llama3")
    client._client.generate = MagicMock(return_value={"response": "hello"})
    client.generate("prompt")
    call_kwargs = client._client.generate.call_args
    assert call_kwargs.kwargs["model"] == "llama3" or call_kwargs.args[0] == "llama3" or \
           client._client.generate.call_args[1].get("model") == "llama3" or \
           "llama3" in str(call_kwargs)


def test_generate_passes_prompt():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"response": "ok"})
    client.generate("my test prompt")
    call_kwargs = client._client.generate.call_args
    assert "my test prompt" in str(call_kwargs)


# ── Model not found ───────────────────────────────────────────────────────────

def test_generate_raises_model_not_found():
    from ollama import ResponseError
    client = _make_client()
    client._client.generate = MagicMock(
        side_effect=ResponseError("model 'qwen3:8b' not found")
    )
    with pytest.raises(ModelNotFoundError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.model == "qwen3:8b"


# ── Connection failures ───────────────────────────────────────────────────────

def test_generate_raises_unavailable_on_connection_error():
    client = _make_client()
    client._client.generate = MagicMock(
        side_effect=ConnectionError("connection refused")
    )
    with pytest.raises(OllamaUnavailableError):
        client.generate("prompt")


def test_generate_raises_unavailable_on_generic_connection_string():
    client = _make_client()
    client._client.generate = MagicMock(
        side_effect=Exception("Failed to connect to server")
    )
    with pytest.raises(OllamaUnavailableError):
        client.generate("prompt")


# ── Timeout ───────────────────────────────────────────────────────────────────

def test_generate_raises_timeout():
    client = _make_client()
    client._client.generate = MagicMock(
        side_effect=TimeoutError("timed out")
    )
    with pytest.raises(OllamaTimeoutError) as exc_info:
        client.generate("prompt")
    assert exc_info.value.model == "qwen3:8b"


def test_generate_raises_timeout_on_string_match():
    client = _make_client()
    client._client.generate = MagicMock(
        side_effect=Exception("request timed out after 120s")
    )
    with pytest.raises(OllamaTimeoutError):
        client.generate("prompt")


# ── Malformed response ────────────────────────────────────────────────────────

def test_generate_raises_malformed_on_missing_response_key():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"wrong_key": "data"})
    with pytest.raises(MalformedResponseError):
        client.generate("prompt")


def test_generate_raises_malformed_on_empty_response():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"response": ""})
    with pytest.raises(MalformedResponseError):
        client.generate("prompt")


def test_generate_raises_malformed_on_whitespace_response():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"response": "   "})
    with pytest.raises(MalformedResponseError):
        client.generate("prompt")


def test_generate_raises_malformed_on_none_response():
    client = _make_client()
    client._client.generate = MagicMock(return_value={"response": None})
    with pytest.raises(MalformedResponseError):
        client.generate("prompt")
