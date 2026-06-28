"""Input and output validation for the PDF extraction module."""

from __future__ import annotations

import os
from pathlib import Path

from src.extraction.exceptions import (
    InvalidPDFError,
    OutputWriteError,
    PDFNotFoundError,
    SchemaValidationError,
)


def validate_input_path(pdf_path: str | Path) -> Path:
    """Validate that pdf_path points to a readable, non-empty PDF file.

    Returns the resolved Path on success.
    Raises PDFNotFoundError or InvalidPDFError on failure.
    """
    path = Path(pdf_path).resolve()

    if not path.exists() or not path.is_file():
        raise PDFNotFoundError(path)

    if not os.access(path, os.R_OK):
        raise PDFNotFoundError(path)

    if path.suffix.lower() != ".pdf":
        raise InvalidPDFError(path)

    if path.stat().st_size == 0:
        raise InvalidPDFError(path)

    return path


def validate_output_dir(output_dir: str | Path) -> Path:
    """Ensure output_dir exists and is writable, creating it if needed.

    Returns the resolved Path on success.
    Raises OutputWriteError on failure.
    """
    path = Path(output_dir).resolve()

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OutputWriteError(path, original_error=e) from e

    if not path.is_dir():
        raise OutputWriteError(path)

    if not os.access(path, os.W_OK):
        raise OutputWriteError(path)

    return path


def validate_output_payload(payload: dict) -> None:
    """Validate the assembled output payload before it is written to disk.

    Checks required schema metadata fields. All resume fields are optional.
    Raises SchemaValidationError on the first invalid field found.
    """
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise SchemaValidationError("schema_version", "must be a non-empty string")

    parser_version = payload.get("parser_version")
    if not isinstance(parser_version, str) or not parser_version.strip():
        raise SchemaValidationError("parser_version", "must be a non-empty string")

    extracted_at = payload.get("extracted_at")
    if extracted_at is None:
        raise SchemaValidationError("extracted_at", "must be present")

    raw_text = payload.get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise SchemaValidationError("raw_text", "must be a non-empty string")
