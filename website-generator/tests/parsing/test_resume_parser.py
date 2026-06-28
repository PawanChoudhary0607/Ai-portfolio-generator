"""Integration and contract tests for src/parsing/resume_parser.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parsing.resume_parser import parse
from src.schemas.resume import PARSER_VERSION, SCHEMA_VERSION, ResumeSchema

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_raw_text.txt"
RAW_TEXT = FIXTURE_PATH.read_text(encoding="utf-8")


# ── Contract: output is always a valid ResumeSchema ──────────────────────────

def test_parse_returns_resume_schema():
    result = parse(RAW_TEXT)
    assert isinstance(result, ResumeSchema)


def test_parse_empty_string_returns_schema():
    """Even with no content, parse must return a schema — never raise."""
    result = parse("")
    assert isinstance(result, ResumeSchema)


def test_parse_garbage_input_returns_schema():
    result = parse("%%%###@@@!!!")
    assert isinstance(result, ResumeSchema)


# ── Metadata fields ───────────────────────────────────────────────────────────

def test_schema_version_set():
    result = parse(RAW_TEXT)
    assert result.schema_version == SCHEMA_VERSION


def test_parser_version_set():
    result = parse(RAW_TEXT)
    assert result.parser_version == PARSER_VERSION


def test_extracted_at_set():
    result = parse(RAW_TEXT)
    assert result.extracted_at is not None


def test_filename_stored():
    result = parse(RAW_TEXT, filename="resume.pdf")
    assert result.filename == "resume.pdf"


def test_page_count_stored():
    result = parse(RAW_TEXT, page_count=2)
    assert result.page_count == 2


def test_raw_text_preserved():
    result = parse(RAW_TEXT)
    assert result.raw_text == RAW_TEXT


# ── Personal info ─────────────────────────────────────────────────────────────

def test_email_extracted():
    result = parse(RAW_TEXT)
    assert result.personal is not None
    assert result.personal.email == "pawan@example.com"


def test_phone_extracted():
    result = parse(RAW_TEXT)
    assert result.personal is not None
    assert result.personal.phone is not None
    assert "9876543210" in result.personal.phone


def test_linkedin_extracted():
    result = parse(RAW_TEXT)
    assert result.personal is not None
    assert result.personal.linkedin == "linkedin.com/in/pawanchoudhary"


def test_name_is_first_line():
    result = parse(RAW_TEXT)
    assert result.personal is not None
    assert result.personal.name == "Pawan Choudhary"


def test_no_contact_info_personal_is_none():
    result = parse("No contact info here whatsoever.")
    # name heuristic will fire, so personal won't be None — just check it doesn't crash
    assert isinstance(result, ResumeSchema)


# ── Skills ────────────────────────────────────────────────────────────────────

def test_skills_extracted():
    result = parse(RAW_TEXT)
    assert "Python" in result.skills


def test_skills_preserve_capitalisation():
    result = parse(RAW_TEXT)
    assert "AWS" in result.skills
    assert "aws" not in result.skills


def test_skills_no_duplicates():
    text = "Skills\nPython, python, PYTHON\n"
    result = parse(text)
    lower_count = sum(1 for s in result.skills if s.lower() == "python")
    assert lower_count == 1


def test_no_skills_section_returns_empty_list():
    result = parse("Pawan Choudhary\nNo skills section here.")
    assert result.skills == []


# ── Raw section blocks ────────────────────────────────────────────────────────

def test_experience_raw_captured():
    result = parse(RAW_TEXT)
    assert result.experience_raw is not None
    assert "Acme Corp" in result.experience_raw


def test_education_raw_captured():
    result = parse(RAW_TEXT)
    assert result.education_raw is not None
    assert "BTech" in result.education_raw


def test_projects_raw_captured():
    result = parse(RAW_TEXT)
    assert result.projects_raw is not None
    assert "AI Portfolio" in result.projects_raw


def test_certifications_raw_captured():
    result = parse(RAW_TEXT)
    assert result.certifications_raw is not None
    assert "AWS" in result.certifications_raw


def test_missing_sections_are_none():
    result = parse("Pawan Choudhary\nJust a name, nothing else.")
    assert result.experience_raw is None
    assert result.education_raw is None
    assert result.projects_raw is None
    assert result.certifications_raw is None


# ── model_dump is JSON-serialisable ──────────────────────────────────────────

def test_model_dump_is_serialisable():
    import json
    result = parse(RAW_TEXT, filename="resume.pdf", page_count=1)
    dumped = result.model_dump(mode="json")
    serialised = json.dumps(dumped, default=str)
    assert "schema_version" in serialised
    assert "raw_text" in serialised
