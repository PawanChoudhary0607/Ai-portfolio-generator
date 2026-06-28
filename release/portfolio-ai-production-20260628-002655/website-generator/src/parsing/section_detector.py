"""Detect and split resume sections from raw extracted text.

Strategy: regex against a known dictionary of section header variants.
Returns a dict mapping canonical section names to their raw text blocks.
Never raises — missing sections return None for that key.
"""

from __future__ import annotations

import re

# Canonical section name → list of header patterns to match (case-insensitive)
SECTION_PATTERNS: dict[str, list[str]] = {
    "personal": [
        r"contact(?: information| info)?",
        r"personal(?: information| info| details)?",
    ],
    "summary": [
        r"(?:professional )?summary",
        r"objective",
        r"profile",
        r"about(?: me)?",
    ],
    "skills": [
        r"(?:technical )?skills?",
        r"core competencies",
        r"technologies",
        r"tech(?:nical)? stack",
        r"tools?(?: & technologies)?",
    ],
    "experience": [
        r"(?:work |professional |relevant )?experience",
        r"work history",
        r"employment(?: history)?",
        r"career history",
    ],
    "education": [
        r"education(?:al background)?",
        r"academic(?:s| background)?",
        r"qualifications?",
    ],
    "projects": [
        r"projects?",
        r"personal projects?",
        r"key projects?",
        r"notable projects?",
    ],
    "certifications": [
        r"certifications?",
        r"certificates?",
        r"licen[sc]es?(?: & certifications?)?",
        r"credentials?",
    ],
}

# Built once at import time: single regex that matches any known header
# Captures: optional leading whitespace, the header text, optional colon
_ALL_PATTERNS = "|".join(
    f"(?:{p})" for patterns in SECTION_PATTERNS.values() for p in patterns
)
_HEADER_RE = re.compile(
    rf"^[ \t]*({_ALL_PATTERNS}):?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def _canonical(header_text: str) -> str | None:
    """Map a matched header string to its canonical section name."""
    normalised = header_text.strip().lower().rstrip(":")
    for canonical, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalised, re.IGNORECASE):
                return canonical
    return None


def detect(raw_text: str) -> dict[str, str | None]:
    """Split raw_text into named sections.

    Returns a dict with keys for every canonical section name.
    Sections not found in the text have value None.
    """
    result: dict[str, str | None] = {key: None for key in SECTION_PATTERNS}

    matches = list(_HEADER_RE.finditer(raw_text))
    if not matches:
        return result

    for i, match in enumerate(matches):
        canonical = _canonical(match.group(1))
        if canonical is None:
            continue

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()

        if block:
            result[canonical] = block

    return result
