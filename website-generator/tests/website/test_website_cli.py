"""CLI integration tests for the 'website' command (Milestone 5).

Tests the argument parser and cmd_website() logic using mocks
and the fixture portfolio JSON. No Ollama calls are made.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "valid_portfolio.json"


# ── build_parser tests ─────────────────────────────────────────────────────────

def test_parser_has_website_subcommand():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "data/raw/resume.pdf"])
    assert args.command == "website"
    assert args.pdf == "data/raw/resume.pdf"


def test_parser_website_default_theme():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "resume.pdf"])
    assert args.theme == "minimal-white-orange"


def test_parser_website_theme_choices():
    from main import build_parser
    parser = build_parser()
    for theme in ["minimal-white-orange", "executive-black-gold", "developer-dark", "creative-portfolio", "modern-saas"]:
        args = parser.parse_args(["website", "resume.pdf", "--theme", theme])
        assert args.theme == theme


def test_parser_website_invalid_theme_exits():
    from main import build_parser
    import argparse
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["website", "resume.pdf", "--theme", "neon"])


def test_parser_website_output_dir():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "resume.pdf", "--output-dir", "/tmp/out"])
    assert args.output_dir == "/tmp/out"


def test_parser_website_default_output_dir_is_none():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "resume.pdf"])
    assert args.output_dir is None


def test_parser_website_model_arg():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "resume.pdf", "--model", "qwen3:14b"])
    assert args.model == "qwen3:14b"


def test_parser_website_host_arg():
    from main import build_parser
    parser = build_parser()
    args = parser.parse_args(["website", "resume.pdf", "--host", "http://example.com"])
    assert args.host == "http://example.com"


# ── cmd_website with JSON input ────────────────────────────────────────────────

def _make_website_args(
    pdf=None,
    theme="minimal-white-orange",
    output_dir=None,
    model="qwen3:8b",
    host="http://localhost:11434",
):
    args = MagicMock()
    args.pdf = str(pdf or FIXTURE_JSON)
    args.theme = theme
    args.output_dir = output_dir
    args.model = model
    args.host = host
    return args


def test_cmd_website_json_input_returns_0(tmp_path):
    from main import cmd_website
    args = _make_website_args(pdf=FIXTURE_JSON, output_dir=str(tmp_path / "site"))
    result = cmd_website(args)
    assert result == 0


def test_cmd_website_json_creates_index_html(tmp_path):
    from main import cmd_website
    out = tmp_path / "site"
    args = _make_website_args(pdf=FIXTURE_JSON, output_dir=str(out))
    cmd_website(args)
    assert (out / "index.html").exists()


def test_cmd_website_json_creates_styles_css(tmp_path):
    from main import cmd_website
    out = tmp_path / "site"
    args = _make_website_args(pdf=FIXTURE_JSON, output_dir=str(out))
    cmd_website(args)
    assert (out / "styles.css").exists()


def test_cmd_website_json_creates_portfolio_data(tmp_path):
    from main import cmd_website
    out = tmp_path / "site"
    args = _make_website_args(pdf=FIXTURE_JSON, output_dir=str(out))
    cmd_website(args)
    assert (out / "portfolio_data.json").exists()


def test_cmd_website_json_portfolio_data_valid(tmp_path):
    from main import cmd_website
    out = tmp_path / "site"
    args = _make_website_args(pdf=FIXTURE_JSON, output_dir=str(out))
    cmd_website(args)
    data = json.loads((out / "portfolio_data.json").read_text())
    assert "hero" in data
    assert data["hero"]["name"] == "Pawan Choudhary"


def test_cmd_website_all_themes_from_json(tmp_path):
    from main import cmd_website
    for theme in ["minimal-white-orange", "executive-black-gold", "developer-dark", "creative-portfolio", "modern-saas"]:
        out = tmp_path / theme
        args = _make_website_args(pdf=FIXTURE_JSON, theme=theme, output_dir=str(out))
        result = cmd_website(args)
        assert result == 0
        assert (out / "index.html").exists()


def test_cmd_website_invalid_theme_returns_1(tmp_path):
    from main import cmd_website
    args = _make_website_args(pdf=FIXTURE_JSON, theme="cyberpunk", output_dir=str(tmp_path / "s"))
    result = cmd_website(args)
    assert result == 1


def test_cmd_website_missing_json_returns_1(tmp_path):
    from main import cmd_website
    args = _make_website_args(
        pdf=str(tmp_path / "nonexistent.json"),
        output_dir=str(tmp_path / "site"),
    )
    result = cmd_website(args)
    assert result == 1


def test_cmd_website_bad_json_returns_1(tmp_path):
    from main import cmd_website
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }", encoding="utf-8")
    args = _make_website_args(pdf=str(bad), output_dir=str(tmp_path / "site"))
    result = cmd_website(args)
    assert result == 1


# ── cmd_website with PDF input (mocked pipeline) ──────────────────────────────

try:
    import fitz  # noqa: F401
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

pytestmark_pdf = pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF (fitz) not installed")


@pytestmark_pdf
def test_cmd_website_pdf_extraction_failure_returns_1(tmp_path):
    from main import cmd_website
    from src.extraction.exceptions import ExtractionError

    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"not a pdf")
    args = _make_website_args(pdf=str(pdf), output_dir=str(tmp_path / "site"))

    # main.py uses local imports inside cmd_website, so patch at source module
    with patch("src.extraction.validator.validate_input_path", side_effect=ExtractionError("bad pdf")):
        result = cmd_website(args)
    assert result == 1


@pytestmark_pdf
def test_cmd_website_pdf_ai_failure_returns_1(tmp_path):
    from main import cmd_website
    from src.ai.exceptions import AIError
    from src.schemas.resume import ResumeSchema

    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    args = _make_website_args(pdf=str(pdf), output_dir=str(tmp_path / "site"))

    mock_resume = MagicMock(spec=ResumeSchema)
    mock_resume.personal = None
    mock_resume.skills = []

    with patch("src.extraction.validator.validate_input_path", return_value=pdf), \
         patch("src.extraction.validator.validate_output_dir", return_value=tmp_path), \
         patch("src.extraction.pdf_extractor.read_pdf", return_value=(1, "resume text")), \
         patch("src.parsing.resume_parser.parse", return_value=mock_resume), \
         patch("src.ai.analyzer.analyze", side_effect=AIError("ollama down")):
        result = cmd_website(args)
    assert result == 1


# ── main() routing ────────────────────────────────────────────────────────────

def test_main_routes_website_command(tmp_path):
    from main import main
    import sys
    args_backup = sys.argv[:]
    sys.argv = ["main.py", "website", str(FIXTURE_JSON), "--output-dir", str(tmp_path / "site")]
    try:
        result = main()
    finally:
        sys.argv = args_backup
    assert result == 0
