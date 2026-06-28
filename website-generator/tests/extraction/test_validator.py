"""Unit tests for src/extraction/validator.py."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.extraction.exceptions import (
    InvalidPDFError,
    OutputWriteError,
    PDFNotFoundError,
    SchemaValidationError,
)
from src.extraction.validator import (
    validate_input_path,
    validate_output_dir,
    validate_output_payload,
)


# ── validate_input_path ───────────────────────────────────────────────────────

def test_missing_file_raises_pdf_not_found():
    with pytest.raises(PDFNotFoundError):
        validate_input_path("/tmp/does_not_exist.pdf")


def test_wrong_extension_raises_invalid_pdf():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"data")
        name = f.name
    try:
        with pytest.raises(InvalidPDFError):
            validate_input_path(name)
    finally:
        os.unlink(name)


def test_zero_byte_pdf_raises_invalid_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        name = f.name
    try:
        with pytest.raises(InvalidPDFError):
            validate_input_path(name)
    finally:
        os.unlink(name)


def test_valid_pdf_returns_resolved_path():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake content")
        name = f.name
    try:
        result = validate_input_path(name)
        assert isinstance(result, Path)
        assert result.suffix == ".pdf"
    finally:
        os.unlink(name)


def test_uppercase_pdf_extension_accepted():
    with tempfile.NamedTemporaryFile(suffix=".PDF", delete=False) as f:
        f.write(b"%PDF-1.4 fake content")
        name = f.name
    try:
        result = validate_input_path(name)
        assert result.exists()
    finally:
        os.unlink(name)


# ── validate_output_dir ───────────────────────────────────────────────────────

def test_existing_dir_returned_as_path():
    with tempfile.TemporaryDirectory() as d:
        result = validate_output_dir(d)
        assert result.is_dir()


def test_missing_dir_is_created():
    with tempfile.TemporaryDirectory() as d:
        nested = Path(d) / "a" / "b" / "c"
        result = validate_output_dir(nested)
        assert result.is_dir()


def test_returns_resolved_path():
    with tempfile.TemporaryDirectory() as d:
        result = validate_output_dir(d)
        assert result == Path(d).resolve()


# ── validate_output_payload ───────────────────────────────────────────────────

VALID_PAYLOAD = {
    "schema_version": "2.0",
    "parser_version": "1.0",
    "extracted_at": "2026-06-15T09:00:00Z",
    "filename": "resume.pdf",
    "page_count": 1,
    "raw_text": "Jane Doe\nSoftware Engineer",
    "personal": None,
    "summary": None,
    "skills": [],
    "experience_raw": None,
    "education_raw": None,
    "projects_raw": None,
    "certifications_raw": None,
}


def test_valid_payload_passes():
    validate_output_payload(VALID_PAYLOAD)  # no exception


def test_missing_schema_version_raises():
    payload = {**VALID_PAYLOAD, "schema_version": ""}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_output_payload(payload)
    assert exc_info.value.field == "schema_version"


def test_missing_parser_version_raises():
    payload = {**VALID_PAYLOAD, "parser_version": ""}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_output_payload(payload)
    assert exc_info.value.field == "parser_version"


def test_missing_extracted_at_raises():
    payload = {**VALID_PAYLOAD, "extracted_at": None}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_output_payload(payload)
    assert exc_info.value.field == "extracted_at"


def test_empty_raw_text_raises():
    payload = {**VALID_PAYLOAD, "raw_text": ""}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_output_payload(payload)
    assert exc_info.value.field == "raw_text"


def test_whitespace_raw_text_raises():
    payload = {**VALID_PAYLOAD, "raw_text": "   \n\t  "}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_output_payload(payload)
    assert exc_info.value.field == "raw_text"
