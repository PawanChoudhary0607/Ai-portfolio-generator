"""Unit tests for the 'portfolio' CLI command in main.py.

All Ollama calls, PDF extraction, and AI analysis are mocked.
No real PDF, no network, no Ollama server required.

Patching strategy:
  cmd_portfolio() uses lazy imports, so each imported name must be patched
  at the *source* module where it is defined, not on `main`:
    src.extraction.validator.validate_input_path
    src.extraction.validator.validate_output_dir
    src.extraction.pdf_extractor.read_pdf
    src.parsing.resume_parser.parse
    src.ai.analyzer.analyze
    src.portfolio.portfolio_generator.generate_and_save
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import build_parser, cmd_portfolio, main
from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.exceptions import OllamaUnavailableError
from src.extraction.exceptions import PDFNotFoundError
from src.portfolio.exceptions import PortfolioGenerationError
from src.portfolio.portfolio_schema import (
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)
from src.schemas.resume import PersonalInfo, ResumeSchema

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "valid_portfolio_response.json"
VALID_PORTFOLIO_RESPONSE = FIXTURE_PATH.read_text(encoding="utf-8")

AI_FIXTURE_PATH = (
    Path(__file__).parent.parent / "ai" / "fixtures" / "valid_response.json"
)
VALID_AI_RESPONSE = AI_FIXTURE_PATH.read_text(encoding="utf-8")


# ── Patch targets (lazy-import style — patch at definition site) ───────────────
_VALIDATE_INPUT  = "src.extraction.validator.validate_input_path"
_VALIDATE_OUTPUT = "src.extraction.validator.validate_output_dir"
_READ_PDF        = "src.extraction.pdf_extractor.read_pdf"
_PARSE           = "src.parsing.resume_parser.parse"
_ANALYZE         = "src.ai.analyzer.analyze"
_GEN_SAVE        = "src.portfolio.portfolio_generator.generate_and_save"


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_resume() -> ResumeSchema:
    return ResumeSchema(
        filename="sample.pdf",
        page_count=2,
        raw_text="Pawan Choudhary\nPython, ML",
        personal=PersonalInfo(
            name="Pawan Choudhary",
            email="pawan@example.com",
            location="Delhi, India",
        ),
        skills=["Python", "ML"],
        projects_raw="AI Portfolio Generator",
    )


def _make_analysis() -> AIAnalysisSchema:
    return AIAnalysisSchema(
        strengths=["Python", "ML"],
        weaknesses=["No cloud"],
        missing_skills=["Docker"],
        recommended_projects=["Build FastAPI service"],
        recommended_career_paths=["ML Engineer"],
        portfolio_sections=["About", "Skills"],
        summary="Pawan is an emerging AI/ML engineer.",
        llm_model="qwen3:8b",
    )


def _make_portfolio() -> PortfolioSchema:
    return PortfolioSchema(
        hero=HeroSection(
            name="Pawan Choudhary",
            role="ML Engineer",
            headline="Building AI-powered tools.",
        ),
        about="Pawan is an emerging AI/ML engineer.",
        skills=[SkillCategory(category="Programming Languages", items=["Python", "ML"])],
        projects=[
            ProjectItem(
                title="Build FastAPI service",
                problem="Needed a deployable API for the portfolio.",
                technologies=["FastAPI"],
                outcome="Shipped a working microservice.",
            )
        ],
        career_paths=["ML Engineer"],
        contact=ContactInfo(email="pawan@example.com"),
        llm_model="qwen3:8b",
    )


def _make_portfolio_json(tmp_path: Path, portfolio: PortfolioSchema) -> Path:
    """Write portfolio JSON to tmp_path and return the path."""
    p = tmp_path / "sample_portfolio.json"
    p.write_text(
        json.dumps(portfolio.model_dump(mode="json"), default=str),
        encoding="utf-8",
    )
    return p


def _run_cmd_portfolio(tmp_path: Path, model: str = "qwen3:8b") -> int:
    """Run cmd_portfolio with all I/O mocked. Returns the exit code."""
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    resume   = _make_resume()
    analysis = _make_analysis()
    portfolio = _make_portfolio()
    port_path = _make_portfolio_json(tmp_path, portfolio)

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf),
        "--model", model,
        "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(2, "Pawan Choudhary\nPython, ML")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE,         return_value=analysis),
        patch(_GEN_SAVE,        return_value=port_path),
    ):
        return cmd_portfolio(args)


# ── build_parser() — portfolio subcommand ─────────────────────────────────────

def test_parser_has_portfolio_subcommand():
    parser = build_parser()
    args = parser.parse_args(["portfolio", "resume.pdf"])
    assert args.command == "portfolio"


def test_parser_portfolio_pdf_positional():
    args = build_parser().parse_args(["portfolio", "my_resume.pdf"])
    assert args.pdf == "my_resume.pdf"


def test_parser_portfolio_default_model():
    args = build_parser().parse_args(["portfolio", "resume.pdf"])
    assert args.model == "qwen3:8b"


def test_parser_portfolio_custom_model():
    args = build_parser().parse_args(["portfolio", "resume.pdf", "--model", "qwen3:14b"])
    assert args.model == "qwen3:14b"


def test_parser_portfolio_default_host():
    args = build_parser().parse_args(["portfolio", "resume.pdf"])
    assert args.host == "http://localhost:11434"


def test_parser_portfolio_custom_host():
    args = build_parser().parse_args(
        ["portfolio", "resume.pdf", "--host", "http://myhost:11434"]
    )
    assert args.host == "http://myhost:11434"


def test_parser_portfolio_default_output_dir():
    args = build_parser().parse_args(["portfolio", "resume.pdf"])
    assert args.output_dir == "data/processed"


def test_parser_portfolio_custom_output_dir(tmp_path):
    args = build_parser().parse_args(
        ["portfolio", "resume.pdf", "--output-dir", str(tmp_path)]
    )
    assert args.output_dir == str(tmp_path)


# ── cmd_portfolio() happy path ─────────────────────────────────────────────────

def test_cmd_portfolio_returns_zero_on_success(tmp_path):
    assert _run_cmd_portfolio(tmp_path) == 0


def test_cmd_portfolio_output_file_exists(tmp_path):
    _run_cmd_portfolio(tmp_path)
    port_files = list(tmp_path.glob("*_portfolio.json"))
    assert len(port_files) == 1


def test_cmd_portfolio_output_is_valid_json(tmp_path):
    _run_cmd_portfolio(tmp_path)
    port_file = next(tmp_path.glob("*_portfolio.json"))
    data = json.loads(port_file.read_text(encoding="utf-8"))
    assert "hero" in data
    assert "skills" in data
    assert "projects" in data


def test_cmd_portfolio_passes_model_to_analyze(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    resume    = _make_resume()
    analysis  = _make_analysis()
    portfolio = _make_portfolio()
    port_path = _make_portfolio_json(tmp_path, portfolio)

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--model", "qwen3:14b",
        "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(2, "text")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE,         return_value=analysis) as mock_analyze,
        patch(_GEN_SAVE,        return_value=port_path),
    ):
        cmd_portfolio(args)

    call_kwargs = mock_analyze.call_args
    assert "qwen3:14b" in str(call_kwargs)


def test_cmd_portfolio_passes_model_to_generate_and_save(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    resume    = _make_resume()
    analysis  = _make_analysis()
    portfolio = _make_portfolio()
    port_path = _make_portfolio_json(tmp_path, portfolio)

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--model", "qwen3:14b",
        "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(2, "text")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE,         return_value=analysis),
        patch(_GEN_SAVE,        return_value=port_path) as mock_gen,
    ):
        cmd_portfolio(args)

    call_kwargs = mock_gen.call_args
    assert "qwen3:14b" in str(call_kwargs)


# ── cmd_portfolio() error paths ────────────────────────────────────────────────

def test_cmd_portfolio_returns_one_on_extraction_error(tmp_path):
    pdf = tmp_path / "missing.pdf"
    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--output-dir", str(tmp_path),
    ])

    with patch(_VALIDATE_INPUT, side_effect=PDFNotFoundError(pdf)):
        result = cmd_portfolio(args)

    assert result == 1


def test_cmd_portfolio_returns_one_on_ollama_error(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    resume = _make_resume()

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(1, "text")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE, side_effect=OllamaUnavailableError("http://localhost:11434")),
    ):
        result = cmd_portfolio(args)

    assert result == 1


def test_cmd_portfolio_returns_one_on_portfolio_generation_error(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    resume   = _make_resume()
    analysis = _make_analysis()

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(1, "text")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE,         return_value=analysis),
        patch(_GEN_SAVE, side_effect=PortfolioGenerationError("empty response from model")),
    ):
        result = cmd_portfolio(args)

    assert result == 1


def test_cmd_portfolio_extraction_error_does_not_call_analyze(tmp_path):
    pdf = tmp_path / "missing.pdf"
    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT, side_effect=PDFNotFoundError(pdf)),
        patch(_ANALYZE) as mock_analyze,
    ):
        cmd_portfolio(args)

    mock_analyze.assert_not_called()


def test_cmd_portfolio_analysis_error_does_not_call_generate(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    resume = _make_resume()

    parser = build_parser()
    args = parser.parse_args([
        "portfolio", str(pdf), "--output-dir", str(tmp_path),
    ])

    with (
        patch(_VALIDATE_INPUT,  return_value=pdf),
        patch(_VALIDATE_OUTPUT, return_value=tmp_path),
        patch(_READ_PDF,        return_value=(1, "text")),
        patch(_PARSE,           return_value=resume),
        patch(_ANALYZE, side_effect=OllamaUnavailableError("http://localhost:11434")),
        patch(_GEN_SAVE) as mock_gen,
    ):
        cmd_portfolio(args)

    mock_gen.assert_not_called()


# ── main() dispatch ────────────────────────────────────────────────────────────

def test_main_dispatches_portfolio_command(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    with (
        patch("main.cmd_portfolio", return_value=0) as mock_cmd,
        patch("sys.argv", ["main.py", "portfolio", str(pdf)]),
    ):
        result = main()

    mock_cmd.assert_called_once()
    assert result == 0


def test_main_no_command_returns_zero():
    with patch("sys.argv", ["main.py"]):
        result = main()
    assert result == 0


def test_main_portfolio_command_is_independent_of_analyze():
    """Ensure 'portfolio' and 'analyze' are separate subcommands."""
    parser = build_parser()
    portfolio_args = parser.parse_args(["portfolio", "resume.pdf"])
    analyze_args   = parser.parse_args(["analyze",   "resume.pdf"])
    assert portfolio_args.command == "portfolio"
    assert analyze_args.command   == "analyze"
