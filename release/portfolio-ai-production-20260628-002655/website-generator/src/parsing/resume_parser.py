"""Parse raw section text into a ResumeSchema.

Orchestrates section_detector → field parsers → normalizer.
Never raises on parse failure — logs a warning and leaves the field as None.
Deep understanding of experience/education/projects is deferred to the LLM milestone.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from src.parsing import normalizer, section_detector
from src.schemas.resume import PARSER_VERSION, SCHEMA_VERSION, PersonalInfo, ResumeSchema

logger = logging.getLogger(__name__)

# ── Regexes for personal field extraction ────────────────────────────────────

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"[\+\(]?[\d\s\-\(\)]{7,15}")
_LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)

# Skills are commonly comma- or newline-separated
_SKILL_SPLIT_RE = re.compile(r"[,\n•·|/]+")


def _parse_personal(block: str | None, raw_text: str) -> PersonalInfo | None:
    """Extract contact fields from the personal section or fall back to raw_text.

    Name extraction is intentionally conservative — first non-empty line
    of the document is used as a heuristic only.
    """
    source = block or raw_text or ""

    email_match = _EMAIL_RE.search(source)
    phone_match = _PHONE_RE.search(source)
    linkedin_match = _LINKEDIN_RE.search(source)

    # Name heuristic: first non-empty line of the full document
    name: str | None = None
    for line in (raw_text or "").splitlines():
        stripped = line.strip()
        if stripped:
            name = stripped
            break

    personal = PersonalInfo(
        name=normalizer.clean_text(name),
        email=normalizer.clean_text(email_match.group(0)) if email_match else None,
        phone=normalizer.clean_text(phone_match.group(0).strip()) if phone_match else None,
        location=None,   # requires more context — deferred to LLM milestone
        linkedin=normalizer.clean_text(linkedin_match.group(0)) if linkedin_match else None,
    )

    # Return None if we found nothing at all
    if not any([personal.name, personal.email, personal.phone, personal.linkedin]):
        return None
    return personal


def _parse_skills(block: str | None) -> list[str]:
    """Split skill block into individual skills, preserving capitalisation."""
    if not block:
        return []
    raw_skills = _SKILL_SPLIT_RE.split(block)
    skills = [s.strip() for s in raw_skills if s.strip()]
    return normalizer.clean_skills(skills)


def parse(
    raw_text: str,
    filename: str | None = None,
    page_count: int | None = None,
) -> ResumeSchema:
    """Parse raw_text into a ResumeSchema.

    Args:
        raw_text:   Full text extracted from the PDF.
        filename:   Source PDF filename, stored in schema metadata.
        page_count: Page count from pdf_extractor, stored in schema metadata.

    Returns:
        ResumeSchema — always. Unparseable fields are None.
    """
    sections = section_detector.detect(raw_text)

    try:
        personal = _parse_personal(sections.get("personal"), raw_text)
    except Exception:
        logger.warning("personal field parsing failed", exc_info=True)
        personal = None

    try:
        skills = _parse_skills(sections.get("skills"))
    except Exception:
        logger.warning("skills parsing failed", exc_info=True)
        skills = []

    try:
        summary = normalizer.clean_text(sections.get("summary"))
    except Exception:
        logger.warning("summary parsing failed", exc_info=True)
        summary = None

    return ResumeSchema(
        schema_version=SCHEMA_VERSION,
        parser_version=PARSER_VERSION,
        extracted_at=datetime.now(timezone.utc),
        filename=filename,
        page_count=page_count,
        raw_text=raw_text,
        personal=personal,
        summary=summary,
        skills=skills,
        experience_raw=sections.get("experience"),
        education_raw=sections.get("education"),
        projects_raw=sections.get("projects"),
        certifications_raw=sections.get("certifications"),
    )
