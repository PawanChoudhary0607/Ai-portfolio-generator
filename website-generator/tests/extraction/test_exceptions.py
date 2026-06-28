"""Unit tests for src/extraction/exceptions.py."""

from __future__ import annotations

import pytest

from src.extraction.exceptions import (
    EmptyPDFError,
    ExtractionError,
    InvalidPDFError,
    OutputWriteError,
    PDFNotFoundError,
    SchemaValidationError,
)


def test_all_inherit_from_extraction_error():
    for cls in [
        PDFNotFoundError,
        InvalidPDFError,
        EmptyPDFError,
        SchemaValidationError,
        OutputWriteError,
    ]:
        assert issubclass(cls, ExtractionError)


def test_pdf_not_found_stores_path():
    exc = PDFNotFoundError("/tmp/missing.pdf")
    assert str(exc.pdf_path) == "/tmp/missing.pdf"
    assert "missing.pdf" in str(exc)


def test_invalid_pdf_stores_original_error():
    cause = ValueError("corrupt")
    exc = InvalidPDFError("/tmp/bad.pdf", original_error=cause)
    assert exc.original_error is cause


def test_invalid_pdf_no_original_error():
    exc = InvalidPDFError("/tmp/bad.pdf")
    assert exc.original_error is None


def test_empty_pdf_stores_page_count():
    exc = EmptyPDFError("/tmp/scan.pdf", page_count=3)
    assert exc.page_count == 3
    assert "3 pages" in str(exc)


def test_empty_pdf_singular_page():
    exc = EmptyPDFError("/tmp/scan.pdf", page_count=1)
    assert "1 page" in str(exc)
    assert "1 pages" not in str(exc)


def test_schema_validation_error_stores_field():
    exc = SchemaValidationError("raw_text", "must be non-empty")
    assert exc.field == "raw_text"
    assert "raw_text" in str(exc)


def test_output_write_error_stores_path_and_original():
    cause = OSError("disk full")
    exc = OutputWriteError("/data/out.json", original_error=cause)
    assert exc.original_error is cause
    assert "out.json" in str(exc)


def test_broad_catch_works_for_all():
    exceptions = [
        PDFNotFoundError("/tmp/x.pdf"),
        InvalidPDFError("/tmp/x.pdf"),
        EmptyPDFError("/tmp/x.pdf", page_count=1),
        SchemaValidationError("field", "reason"),
        OutputWriteError("/tmp/x.json"),
    ]
    for exc in exceptions:
        with pytest.raises(ExtractionError):
            raise exc
