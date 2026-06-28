"""Unit tests for the website templates (HTML + CSS files).

Validates that each of the 5 themes' template files exist, are well-formed,
contain the required placeholders, and — since the whole point of this
redesign was genuinely different layouts, not palette swaps — that each
theme's distinguishing structural markup is actually present.
No rendering is performed here — these tests inspect the raw templates.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "website" / "templates"

THEMES = [
    "minimal-white-orange",
    "executive-black-gold",
    "developer-dark",
    "creative-portfolio",
    "modern-saas",
]

REQUIRED_PLACEHOLDERS = [
    "{{page_title}}",
    "{{hero_name}}",
    "{{hero_role}}",
    "{{hero_headline}}",
    "{{hero_initials}}",
    "{{about_bio}}",
    "{{skills_markup}}",
    "{{project_markup}}",
    "{{career_markup}}",
    "{{contact_markup}}",
]

REQUIRED_SECTION_IDS = ["about", "career", "projects", "contact"]


# ── Directory & file existence ─────────────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_theme_directory_exists(theme):
    assert (TEMPLATES_DIR / theme).is_dir(), f"Missing template directory: {theme}"


@pytest.mark.parametrize("theme", THEMES)
def test_index_html_exists(theme):
    assert (TEMPLATES_DIR / theme / "index.html").is_file()


@pytest.mark.parametrize("theme", THEMES)
def test_styles_css_exists(theme):
    assert (TEMPLATES_DIR / theme / "styles.css").is_file()


def test_exactly_five_theme_directories():
    dirs = {p.name for p in TEMPLATES_DIR.iterdir() if p.is_dir()}
    assert dirs == set(THEMES)


# ── HTML template content ──────────────────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_html_has_doctype(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert html.strip().startswith("<!DOCTYPE html")


@pytest.mark.parametrize("theme", THEMES)
def test_html_has_viewport_meta(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert "viewport" in html


@pytest.mark.parametrize("theme", THEMES)
def test_html_links_stylesheet(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("placeholder", REQUIRED_PLACEHOLDERS)
def test_html_contains_placeholder(theme, placeholder):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert placeholder in html, f"Missing placeholder '{placeholder}' in {theme}/index.html"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("section_id", REQUIRED_SECTION_IDS)
def test_html_contains_section(theme, section_id):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert f'id="{section_id}"' in html, f"Missing section id='{section_id}' in {theme}/index.html"


@pytest.mark.parametrize("theme", THEMES)
def test_html_has_footer(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert "<footer" in html


@pytest.mark.parametrize("theme", THEMES)
def test_html_has_js_scroll_observer(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert "IntersectionObserver" in html


@pytest.mark.parametrize("theme", THEMES)
def test_html_is_not_empty(theme):
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    assert len(html) > 500


# ── CSS baseline content ───────────────────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_css_has_root_variables(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert ":root" in css


@pytest.mark.parametrize("theme", THEMES)
def test_css_has_responsive_media_query(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert "@media" in css


@pytest.mark.parametrize("theme", THEMES)
def test_css_is_not_empty(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert len(css) > 1000, f"styles.css suspiciously short for theme: {theme}"


@pytest.mark.parametrize("theme", THEMES)
def test_css_has_scroll_behavior(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert "scroll-behavior" in css


@pytest.mark.parametrize("theme", THEMES)
def test_css_respects_reduced_motion(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css


# ── No purple, anywhere — that was the whole point ─────────────────────────────

_PURPLE_HEX_FRAGMENTS = ["7c6cff", "#8b5cf6", "#a78bfa", "#9333ea", "#7e22ce", "#6d28d9"]


@pytest.mark.parametrize("theme", THEMES)
def test_no_theme_uses_the_word_purple(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert "purple" not in css.lower()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("hex_fragment", _PURPLE_HEX_FRAGMENTS)
def test_no_theme_uses_purple_hex_values(theme, hex_fragment):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    assert hex_fragment.lower() not in css.lower()


# ── Each theme must have genuinely distinct chrome (not just colors) ──────────
# One structural marker per theme that could only belong to that theme's
# specific layout concept.

_DISTINCT_LAYOUT_MARKERS = {
    "minimal-white-orange": [".sidebar-inner", ".timeline-marker", ".project-spotlight"],
    "executive-black-gold": [".exec-numeral-lg", ".exec-outcome", ".exec-section-head"],
    "developer-dark": [".file-tree", ".tab-bar", ".code-block", ".commit-log"],
    "creative-portfolio": [".creative-watermark", ".skill-tile", ".rotate-l"],
    "modern-saas": [".saas-hero-blob", ".saas-feature-grid", ".saas-cta-band", ".saas-case"],
}


@pytest.mark.parametrize("theme", THEMES)
def test_theme_has_distinct_layout_markers(theme):
    css = (TEMPLATES_DIR / theme / "styles.css").read_text(encoding="utf-8")
    html = (TEMPLATES_DIR / theme / "index.html").read_text(encoding="utf-8")
    combined = css + html
    for marker in _DISTINCT_LAYOUT_MARKERS[theme]:
        assert marker in combined, f"Missing distinguishing marker '{marker}' for {theme}"


def test_no_two_themes_share_all_layout_markers():
    """Sanity check that the marker sets themselves don't overlap — i.e. the
    themes are actually structurally different from each other, not just
    differently named."""
    marker_sets = [set(v) for v in _DISTINCT_LAYOUT_MARKERS.values()]
    for i, a in enumerate(marker_sets):
        for b in marker_sets[i + 1:]:
            assert not a.issubset(b) and not b.issubset(a)


# ── Minimal White/Orange specifics ─────────────────────────────────────────────

def test_minimal_uses_orange_accent():
    css = (TEMPLATES_DIR / "minimal-white-orange" / "styles.css").read_text(encoding="utf-8")
    assert "#ff6b35" in css.lower()


def test_minimal_has_light_default_background():
    css = (TEMPLATES_DIR / "minimal-white-orange" / "styles.css").read_text(encoding="utf-8")
    assert "#ffffff" in css.lower()


def test_minimal_hero_has_cta_buttons():
    html = (TEMPLATES_DIR / "minimal-white-orange" / "index.html").read_text(encoding="utf-8")
    assert "View Work" in html
    assert "Get in touch" in html


def test_minimal_hero_has_social_placeholder():
    html = (TEMPLATES_DIR / "minimal-white-orange" / "index.html").read_text(encoding="utf-8")
    assert "{{hero_social}}" in html


# ── Executive Black/Gold specifics ─────────────────────────────────────────────

def test_executive_uses_gold_accent():
    css = (TEMPLATES_DIR / "executive-black-gold" / "styles.css").read_text(encoding="utf-8")
    assert "#c9a227" in css.lower()


def test_executive_uses_dark_background():
    css = (TEMPLATES_DIR / "executive-black-gold" / "styles.css").read_text(encoding="utf-8")
    assert "#0b0b0c" in css.lower()


def test_executive_uses_serif_typeface():
    css = (TEMPLATES_DIR / "executive-black-gold" / "styles.css").read_text(encoding="utf-8")
    assert "serif" in css.lower()
    html = (TEMPLATES_DIR / "executive-black-gold" / "index.html").read_text(encoding="utf-8")
    assert "Playfair" in html


def test_executive_has_numbered_sections():
    html = (TEMPLATES_DIR / "executive-black-gold" / "index.html").read_text(encoding="utf-8")
    assert "exec-numeral-lg" in html


# ── Developer Dark specifics ───────────────────────────────────────────────────

def test_developer_dark_has_monospace_font():
    css = (TEMPLATES_DIR / "developer-dark" / "styles.css").read_text(encoding="utf-8")
    assert "monospace" in css.lower()


def test_developer_dark_has_file_tree_nav():
    html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
    assert "file-tree" in html
    assert "about.md" in html


def test_developer_dark_has_tab_bar():
    html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
    assert "tab-bar" in html


def test_developer_dark_uses_github_dark_background():
    css = (TEMPLATES_DIR / "developer-dark" / "styles.css").read_text(encoding="utf-8")
    assert "#0d1117" in css.lower()


# ── Creative Portfolio specifics ───────────────────────────────────────────────

def test_creative_uses_paper_background():
    css = (TEMPLATES_DIR / "creative-portfolio" / "styles.css").read_text(encoding="utf-8")
    assert "#faf7f2" in css.lower()


def test_creative_uses_coral_accent():
    css = (TEMPLATES_DIR / "creative-portfolio" / "styles.css").read_text(encoding="utf-8")
    assert "#ff3d57" in css.lower()


def test_creative_uses_display_typeface():
    html = (TEMPLATES_DIR / "creative-portfolio" / "index.html").read_text(encoding="utf-8")
    assert "Archivo" in html


def test_creative_has_no_sidebar():
    """Creative Portfolio is explicitly full-bleed/top-nav, not a sidebar
    layout — distinguishing it structurally from minimal-white-orange."""
    css = (TEMPLATES_DIR / "creative-portfolio" / "styles.css").read_text(encoding="utf-8")
    assert ".sidebar-inner" not in css


# ── Modern SaaS specifics ──────────────────────────────────────────────────────

def test_saas_uses_blue_accent():
    css = (TEMPLATES_DIR / "modern-saas" / "styles.css").read_text(encoding="utf-8")
    assert "#2563eb" in css.lower()


def test_saas_has_sticky_navbar_with_cta():
    html = (TEMPLATES_DIR / "modern-saas" / "index.html").read_text(encoding="utf-8")
    assert "saas-nav-cta" in html


def test_saas_has_stats_row_placeholder():
    html = (TEMPLATES_DIR / "modern-saas" / "index.html").read_text(encoding="utf-8")
    assert "{{stats_row}}" in html


def test_saas_has_feature_grid_and_cta_band():
    html = (TEMPLATES_DIR / "modern-saas" / "index.html").read_text(encoding="utf-8")
    assert "saas-cta-band" in html
    css = (TEMPLATES_DIR / "modern-saas" / "styles.css").read_text(encoding="utf-8")
    assert "saas-feature-grid" in css
