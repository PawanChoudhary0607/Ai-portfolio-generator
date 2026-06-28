"""Validate and parse raw LLM output into AIAnalysisSchema.

This module is the only place raw model text is turned into structured data.
Any failure here raises an explicit typed exception — never returns partial data.
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.exceptions import MalformedResponseError, SchemaValidationError

# Strip optional markdown code fences the model may emit despite instructions
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    """Extract the JSON object from raw model output.

    Handles:
    - Clean JSON response (ideal case)
    - JSON wrapped in markdown code fences
    - Leading/trailing prose with JSON embedded inside
    """
    text = text.strip()

    # Case 1: wrapped in a code fence
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    # Case 2: find the first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def parse_and_validate(raw_response: str, model_used: str = "") -> AIAnalysisSchema:
    """Parse raw LLM text into a validated AIAnalysisSchema.

    Args:
        raw_response: Raw string returned by OllamaClient.generate().
        model_used:   Model name to embed in schema metadata (stored as llm_model).

    Returns:
        Validated AIAnalysisSchema instance.

    Raises:
        MalformedResponseError: response is not valid JSON.
        SchemaValidationError: JSON is valid but fails schema validation.
    """
    if not raw_response or not raw_response.strip():
        raise MalformedResponseError("empty response from model", raw_response=raw_response)

    json_str = _extract_json(raw_response)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise MalformedResponseError(
            f"JSON decode error: {e}", raw_response=raw_response
        ) from e

    if not isinstance(data, dict):
        raise MalformedResponseError(
            f"expected JSON object, got {type(data).__name__}", raw_response=raw_response
        )

    # Inject metadata before Pydantic validation
    data.setdefault("llm_model", model_used)

    required_list_fields = [
        "strengths",
        "weaknesses",
        "missing_skills",
        "recommended_projects",
        "recommended_career_paths",
        "portfolio_sections",
    ]

    for field in required_list_fields:
        if field not in data:
            raise SchemaValidationError(f"required field '{field}' is missing")
        if not isinstance(data[field], list):
            raise SchemaValidationError(
                f"field '{field}' must be a list, got {type(data[field]).__name__}"
            )
        if len(data[field]) == 0:
            raise SchemaValidationError(f"field '{field}' must not be empty")

    if "summary" not in data:
        raise SchemaValidationError("required field 'summary' is missing")
    if not isinstance(data["summary"], str) or not data["summary"].strip():
        raise SchemaValidationError("field 'summary' must be a non-empty string")

    try:
        return AIAnalysisSchema(**data)
    except ValidationError as e:
        raise SchemaValidationError(str(e)) from e
