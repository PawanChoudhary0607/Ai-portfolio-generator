"""PDF text extraction pipeline."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import fitz  # PyMuPDF

from src.extraction.exceptions import (
    EmptyPDFError,
    InvalidPDFError,
    OutputWriteError,
)
from src.extraction.validator import (
    validate_input_path,
    validate_output_dir,
    validate_output_payload,
)
from src.parsing.resume_parser import parse
from src.schemas.resume import ResumeSchema

logger = logging.getLogger(__name__)


def read_pdf(pdf_path: Path) -> tuple[int, str]:
    """Open pdf_path with PyMuPDF and return (page_count, raw_text).

    Raises InvalidPDFError if fitz cannot open the file.
    Raises EmptyPDFError if no text is extracted.
    """
    try:
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
            raw_text = "".join(page.get_text() for page in doc)
    except Exception as e:
        raise InvalidPDFError(pdf_path, original_error=e) from e

    if not raw_text.strip():
        raise EmptyPDFError(pdf_path, page_count)

    return page_count, raw_text


def build_output(filename: str, page_count: int, raw_text: str) -> dict:
    """Parse raw text into a ResumeSchema and return it as a dict."""
    schema: ResumeSchema = parse(
        raw_text=raw_text,
        filename=filename,
        page_count=page_count,
    )
    return schema.model_dump(mode="json")


def save_output(payload: dict, output_dir: Path) -> Path:
    """Write payload as JSON to output_dir and return the output path.

    Raises OutputWriteError if the write fails.
    """
    stem = Path(payload["filename"]).stem
    output_path = output_dir / f"{stem}.json"

    try:
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except OSError as e:
        raise OutputWriteError(output_path, original_error=e) from e

    return output_path


def extract(
    pdf_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    """Extract and parse a PDF resume, saving structured JSON to output_dir.

    Returns the path of the written JSON file.
    """
    validated_pdf = validate_input_path(pdf_path)
    validated_dir = validate_output_dir(output_dir)

    logger.info("Extracting: %s", validated_pdf)

    page_count, raw_text = read_pdf(validated_pdf)
    payload = build_output(validated_pdf.name, page_count, raw_text)
    validate_output_payload(payload)
    output_path = save_output(payload, validated_dir)

    logger.info("Saved: %s", output_path)
    return output_path
