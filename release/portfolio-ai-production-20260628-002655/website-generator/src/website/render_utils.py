"""Small, theme-agnostic string helpers shared by website_generator.py and
theme_renderers.py.

Kept in their own module (rather than living in website_generator.py) so
theme_renderers.py can import them without risking a circular import, since
website_generator.py imports theme_renderers.py.
"""

from __future__ import annotations

import re

_HEX_CHARS = "0123456789abcdef"


def escape(text: str) -> str:
    """Minimal HTML escaping for user-supplied strings."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def slugify(title: str) -> str:
    """Turn a title into a lowercase-hyphenated slug for decorative use."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "project"


def clean_tel(phone: str) -> str:
    """Strip formatting characters from a phone number for tel: links."""
    return re.sub(r"[^\d+]", "", phone)


def build_initials(name: str) -> str:
    """Return up to 2 uppercase initials from *name*."""
    parts = name.strip().split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def truncate(text: str, max_len: int, suffix: str = "…") -> str:
    """Truncate *text* to at most *max_len* characters, breaking on a word
    boundary where possible so an AI-generated title never silently breaks
    a layout (overflowing a card, hiding behind a horizontal scrollbar,
    wrapping to three lines and crowding out the rest of the content).

    The full, untruncated text is never lost from the page — callers are
    expected to also place it in a `title="..."` attribute for sighted
    hover users and screen readers.
    """
    text = text.strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - len(suffix)].rstrip()
    # Prefer breaking on the last space so we don't chop mid-word.
    last_space = cut.rfind(" ")
    if last_space > max_len * 0.6:  # only break on space if it's not too far back
        cut = cut[:last_space]
    return cut.rstrip(",;:.-") + suffix


def cap_list(items: list[str], max_items: int) -> tuple[list[str], int]:
    """Cap a list to *max_items*, returning (visible_items, overflow_count).

    Used for technology tags and per-category skill lists so a dense resume
    (e.g. 9 tools in one category) doesn't wrap into an unreadable wall of
    chips — the overflow count is rendered as a single "+N more" chip
    instead of being silently dropped.
    """
    if len(items) <= max_items:
        return items, 0
    return items[:max_items], len(items) - max_items


def name_size_class(name: str, threshold: int = 18) -> str:
    """Return a CSS class name to apply when *name* is long enough to need
    a smaller font size to avoid overflowing its container."""
    return "name-long" if len(name.strip()) > threshold else ""


def headline_size_class(headline: str, threshold: int = 70) -> str:
    """Return a CSS class name to apply when *headline* is long enough to
    need a smaller font size / wider container to avoid awkward wraps."""
    return "headline-long" if len(headline.strip()) > threshold else ""
def fake_hex(seed: str, length: int = 7) -> str:
    """Deterministic, decorative pseudo git-hash derived from *seed*.

    Purely cosmetic (used by the developer-dark theme's commit-log career
    timeline) — never used as a real identifier.
    """
    h = 0
    for ch in seed:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    out = []
    for _ in range(length):
        out.append(_HEX_CHARS[h & 0xF])
        h >>= 4
        if h == 0:
            h = (sum(out.__len__() * 17 for _ in [0]) + 1) * 2654435761 & 0xFFFFFFFF
    return "".join(out)
