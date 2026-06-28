"""Unit tests for src/ai/analyzer.py.

All Ollama calls are mocked. No network dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.analyzer import analyze, analyze_and_save
from src.ai.exceptions import MalformedResponseError, OllamaUnavailableError
from src.schemas.resume import PersonalInfo, ResumeSchema

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "valid_response.json"
VALID_RESPONSE = FIXTURE_PATH.read_text(encoding="utf-8")


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture()
def sample_resume() -> ResumeSchema:
    return ResumeSchema(
        filename="resume.pdf",
        page_count=1,
        raw_text="Pawan Choudhary\nPython, Machine Learning\nAI Portfolio Generator",
        personal=PersonalInfo(name="Pawan Choudhary", email="pawan@example.com"),
        skills=["Python", "Machine Learning", "Git"],
        projects_raw="AI Portfolio Generator",
    )


def _mock_client(response_text: str):
    """Return a patched OllamaClient that returns response_text."""
    mock = MagicMock()
    mock.generate.return_value = response_text
    return mock


# ── analyze() ─────────────────────────────────────────────────────────────────

def test_analyze_returns_ai_analysis_schema(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = analyze(sample_resume)
    assert isinstance(result, AIAnalysisSchema)


def test_analyze_populates_all_fields(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = analyze(sample_resume)
    assert result.strengths
    assert result.weaknesses
    assert result.missing_skills
    assert result.recommended_projects
    assert result.recommended_career_paths
    assert result.portfolio_sections
    assert result.summary


def test_analyze_model_stored_in_result(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = analyze(sample_resume, model="llama3")
    assert result.llm_model == "llama3"


def test_analyze_propagates_ollama_unavailable(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        mock = MagicMock()
        mock.generate.side_effect = OllamaUnavailableError("http://localhost:11434")
        MockClient.return_value = mock
        with pytest.raises(OllamaUnavailableError):
            analyze(sample_resume)


def test_analyze_propagates_malformed_response(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client("this is not json at all")
        with pytest.raises(MalformedResponseError):
            analyze(sample_resume)


def test_analyze_uses_default_model(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        analyze(sample_resume)
    call_kwargs = MockClient.call_args
    assert "qwen3:8b" in str(call_kwargs)


def test_analyze_passes_custom_host(sample_resume):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        analyze(sample_resume, host="http://myhost:11434")
    call_kwargs = MockClient.call_args
    assert "myhost" in str(call_kwargs)


# ── analyze_and_save() ────────────────────────────────────────────────────────

def test_analyze_and_save_writes_json_file(sample_resume, tmp_path):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = analyze_and_save(sample_resume, output_dir=tmp_path)
    assert out.exists()
    assert out.suffix == ".json"


def test_analyze_and_save_filename_uses_stem(sample_resume, tmp_path):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = analyze_and_save(sample_resume, output_dir=tmp_path)
    assert out.name == "resume_analysis.json"


def test_analyze_and_save_output_is_valid_json(sample_resume, tmp_path):
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = analyze_and_save(sample_resume, output_dir=tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "strengths" in data
    assert "summary" in data
    assert "schema_version" in data


def test_analyze_and_save_creates_output_dir(sample_resume, tmp_path):
    nested = tmp_path / "a" / "b"
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = analyze_and_save(sample_resume, output_dir=nested)
    assert out.exists()


def test_analyze_and_save_fallback_stem_when_no_filename(tmp_path):
    resume = ResumeSchema(raw_text="Some resume text", skills=["Python"])
    with patch("src.ai.analyzer.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = analyze_and_save(resume, output_dir=tmp_path)
    assert out.name == "resume_analysis.json"
