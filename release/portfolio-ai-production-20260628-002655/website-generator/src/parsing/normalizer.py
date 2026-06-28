"""Normalise a parsed ResumeSchema before it is written to disk.

Pure functions only — no I/O, no logging, no side effects.
Canonical skill capitalisation is preserved (caller's responsibility to supply it correctly).
"""

from __future__ import annotations

# Unicode ligature and artifact map produced by PyMuPDF on some PDFs
_UNICODE_REPLACEMENTS: dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u00a0": " ",   # non-breaking space
}


def clean_text(text: str | None) -> str | None:
    """Strip whitespace and replace known PyMuPDF unicode artifacts."""
    if text is None:
        return None
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.strip() or None


def clean_skills(skills: list[str]) -> list[str]:
    """Deduplicate skills, preserving canonical capitalisation.

    First occurrence of a skill (case-insensitive) wins.
    Empty strings are removed.
    """
    seen: dict[str, str] = {}
    for skill in skills:
        cleaned = skill.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen[key] = cleaned
    return list(seen.values())


def clean_list(items: list[str]) -> list[str]:
    """Strip and remove empty strings from a list."""
    return [item.strip() for item in items if item.strip()]
