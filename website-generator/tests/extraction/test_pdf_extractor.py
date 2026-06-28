"""Integration tests for src/extraction/pdf_extractor.py."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fitz
import pytest

from src.extraction.exceptions import (
    EmptyPDFError,
    InvalidPDFError,
    PDFNotFoundError,
)
from src.extraction.pdf_extractor import (
    build_output,
    extract,
    read_pdf,
    save_output,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def text_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Jane Doe\nSoftware Engineer\nPython, AWS")
    path = tmp_path / "resume.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def multipage_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page()
        page.insert_text((50, 100), f"Page {i + 1} content here.")
    path = tmp_path / "multi.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def blank_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    doc.new_page()
    path = tmp_path / "blank.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def corrupt_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"not a pdf at all")
    return path


# ── read_pdf ──────────────────────────────────────────────────────────────────

def test_read_pdf_returns_page_count_and_text(text_pdf):
    page_count, raw_text = read_pdf(text_pdf)
    assert page_count == 1
    assert "Jane Doe" in raw_text


def test_read_pdf_multipage_count(multipage_pdf):
    page_count, raw_text = read_pdf(multipage_pdf)
    assert page_count == 2
    assert "Page 1" in raw_text
    assert "Page 2" in raw_text


def test_read_pdf_corrupt_raises_invalid_pdf(corrupt_pdf):
    with pytest.raises(InvalidPDFError) as exc_info:
        read_pdf(corrupt_pdf)
    assert exc_info.value.original_error is not None


def test_read_pdf_blank_raises_empty_pdf(blank_pdf):
    with pytest.raises(EmptyPDFError) as exc_info:
        read_pdf(blank_pdf)
    assert exc_info.value.page_count == 1


# ── build_output ──────────────────────────────────────────────────────────────

def test_build_output_contains_required_keys():
    payload = build_output("resume.pdf", 1, "Jane Doe\nSoftware Engineer")
    for key in ["schema_version", "parser_version", "extracted_at", "raw_text", "filename"]:
        assert key in payload


def test_build_output_raw_text_preserved():
    raw = "Jane Doe\nSoftware Engineer"
    payload = build_output("resume.pdf", 1, raw)
    assert payload["raw_text"] == raw


def test_build_output_filename_stored():
    payload = build_output("resume.pdf", 1, "Some text")
    assert payload["filename"] == "resume.pdf"


def test_build_output_page_count_stored():
    payload = build_output("resume.pdf", 3, "Some text")
    assert payload["page_count"] == 3


# ── save_output ───────────────────────────────────────────────────────────────

def test_save_output_writes_valid_json(tmp_path):
    payload = build_output("resume.pdf", 1, "hello world")
    out = save_output(payload, tmp_path)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["raw_text"] == "hello world"


def test_save_output_filename_uses_stem(tmp_path):
    payload = build_output("my_resume.pdf", 1, "hi there")
    out = save_output(payload, tmp_path)
    assert out.name == "my_resume.json"


# ── extract (full pipeline) ───────────────────────────────────────────────────

def test_extract_happy_path(text_pdf, tmp_path):
    out = extract(text_pdf, tmp_path)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["filename"] == "resume.pdf"
    assert data["page_count"] == 1
    assert "Jane Doe" in data["raw_text"]


def test_extract_creates_output_dir(text_pdf, tmp_path):
    nested = tmp_path / "a" / "b"
    out = extract(text_pdf, nested)
    assert out.exists()


def test_extract_missing_pdf_raises(tmp_path):
    with pytest.raises(PDFNotFoundError):
        extract(tmp_path / "missing.pdf", tmp_path)


def test_extract_blank_pdf_raises(blank_pdf, tmp_path):
    with pytest.raises(EmptyPDFError):
        extract(blank_pdf, tmp_path)


def test_extract_corrupt_pdf_raises(corrupt_pdf, tmp_path):
    with pytest.raises(InvalidPDFError):
        extract(corrupt_pdf, tmp_path)


def test_extract_output_has_schema_metadata(text_pdf, tmp_path):
    out = extract(text_pdf, tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "2.0"
    assert data["parser_version"] == "1.0"
    assert data["extracted_at"] is not None


def test_extract_output_raw_text_present(text_pdf, tmp_path):
    out = extract(text_pdf, tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data["raw_text"], str)
    assert data["raw_text"].strip()
