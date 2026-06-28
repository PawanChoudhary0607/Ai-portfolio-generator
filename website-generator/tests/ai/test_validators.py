"""Unit tests for src/ai/validators.py.

No network calls. No Ollama. Pure input/output testing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.exceptions import MalformedResponseError, SchemaValidationError
from src.ai.validators import parse_and_validate

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "valid_response.json"
VALID_JSON = FIXTURE_PATH.read_text(encoding="utf-8")
VALID_DICT = json.loads(VALID_JSON)


# ── Happy path ────────────────────────────────────────────────────────────────

def test_valid_response_returns_schema():
    result = parse_and_validate(VALID_JSON)
    assert isinstance(result, AIAnalysisSchema)


def test_valid_response_fields_populated():
    result = parse_and_validate(VALID_JSON)
    assert len(result.strengths) > 0
    assert len(result.weaknesses) > 0
    assert len(result.missing_skills) > 0
    assert len(result.recommended_projects) > 0
    assert len(result.recommended_career_paths) > 0
    assert len(result.portfolio_sections) > 0
    assert result.summary.strip()


def test_model_used_stored_in_metadata():
    result = parse_and_validate(VALID_JSON, model_used="qwen3:8b")
    assert result.llm_model == "qwen3:8b"


def test_analyzed_at_is_set():
    result = parse_and_validate(VALID_JSON)
    assert result.analyzed_at is not None


def test_schema_version_is_set():
    result = parse_and_validate(VALID_JSON)
    assert result.schema_version == "3.0"


# ── Markdown fence stripping ──────────────────────────────────────────────────

def test_strips_json_markdown_fence():
    wrapped = f"```json\n{VALID_JSON}\n```"
    result = parse_and_validate(wrapped)
    assert isinstance(result, AIAnalysisSchema)


def test_strips_plain_markdown_fence():
    wrapped = f"```\n{VALID_JSON}\n```"
    result = parse_and_validate(wrapped)
    assert isinstance(result, AIAnalysisSchema)


def test_strips_leading_prose():
    with_prose = f"Here is the analysis:\n{VALID_JSON}"
    result = parse_and_validate(with_prose)
    assert isinstance(result, AIAnalysisSchema)


# ── Malformed JSON ────────────────────────────────────────────────────────────

def test_empty_string_raises_malformed():
    with pytest.raises(MalformedResponseError):
        parse_and_validate("")


def test_whitespace_only_raises_malformed():
    with pytest.raises(MalformedResponseError):
        parse_and_validate("   \n  ")


def test_plain_text_raises_malformed():
    with pytest.raises(MalformedResponseError):
        parse_and_validate("Sorry, I cannot analyze this resume.")


def test_invalid_json_raises_malformed():
    with pytest.raises(MalformedResponseError):
        parse_and_validate('{"strengths": [unclosed')


def test_json_array_raises_malformed():
    with pytest.raises(MalformedResponseError):
        parse_and_validate('["not", "an", "object"]')


# ── Missing fields ────────────────────────────────────────────────────────────

def test_missing_strengths_raises_schema_error():
    data = {**VALID_DICT}
    del data["strengths"]
    with pytest.raises(SchemaValidationError) as exc_info:
        parse_and_validate(json.dumps(data))
    assert "strengths" in str(exc_info.value)


def test_missing_weaknesses_raises_schema_error():
    data = {**VALID_DICT}
    del data["weaknesses"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_missing_missing_skills_raises_schema_error():
    data = {**VALID_DICT}
    del data["missing_skills"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_missing_recommended_projects_raises_schema_error():
    data = {**VALID_DICT}
    del data["recommended_projects"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_missing_recommended_career_paths_raises_schema_error():
    data = {**VALID_DICT}
    del data["recommended_career_paths"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_missing_portfolio_sections_raises_schema_error():
    data = {**VALID_DICT}
    del data["portfolio_sections"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_missing_summary_raises_schema_error():
    data = {**VALID_DICT}
    del data["summary"]
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


# ── Empty fields ──────────────────────────────────────────────────────────────

def test_empty_strengths_list_raises_schema_error():
    data = {**VALID_DICT, "strengths": []}
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_empty_summary_raises_schema_error():
    data = {**VALID_DICT, "summary": ""}
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_whitespace_summary_raises_schema_error():
    data = {**VALID_DICT, "summary": "   "}
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


# ── Wrong types ───────────────────────────────────────────────────────────────

def test_strengths_as_string_raises_schema_error():
    data = {**VALID_DICT, "strengths": "not a list"}
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))


def test_summary_as_list_raises_schema_error():
    data = {**VALID_DICT, "summary": ["not", "a", "string"]}
    with pytest.raises(SchemaValidationError):
        parse_and_validate(json.dumps(data))
