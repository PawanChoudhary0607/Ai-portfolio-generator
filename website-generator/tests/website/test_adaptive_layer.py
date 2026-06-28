"""Tests for the Milestone 6 adaptive intelligence layer.

Covers: content density classification, empty-section removal, length
guards, adaptive spacing hooks, adaptive hero sizing hooks, and working
mobile navigation markup — across all 5 themes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.portfolio.portfolio_schema import (
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)
from src.website.content_density import classify_density
from src.website.render_utils import cap_list, headline_size_class, name_size_class, truncate
from src.website.website_generator import build_website_schema, render
from src.website.website_schema import TemplateTheme

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "website" / "templates"
ALL_THEMES = list(TemplateTheme)


def _portfolio(**overrides) -> PortfolioSchema:
    defaults = dict(
        hero=HeroSection(name="Pawan Choudhary", role="ML Engineer", headline="Building things."),
        about="A short bio.",
        skills=[SkillCategory(category="Tools", items=["Python"])],
        projects=[ProjectItem(title="A Project", problem="P", technologies=["Python"], outcome="O")],
        career_paths=["ML Engineer"],
        contact=ContactInfo(),
    )
    defaults.update(overrides)
    return PortfolioSchema(**defaults)


# ── 1. Content density classification ──────────────────────────────────────

class TestContentDensity:
    def test_minimal_single_project_is_sparse(self):
        schema = build_website_schema(_portfolio())
        assert classify_density(schema) == "sparse"

    def test_rich_profile_is_dense(self):
        portfolio = _portfolio(
            projects=[
                ProjectItem(title=f"Project {i}", problem="P", technologies=["A", "B"], outcome="O")
                for i in range(5)
            ],
            skills=[
                SkillCategory(category=f"Cat {i}", items=["a", "b", "c", "d"]) for i in range(5)
            ],
            career_paths=["A", "B", "C", "D"],
        )
        schema = build_website_schema(portfolio)
        assert classify_density(schema) == "dense"

    def test_moderate_profile_is_medium(self):
        portfolio = _portfolio(
            projects=[
                ProjectItem(title="A", problem="P", technologies=["X"], outcome="O"),
                ProjectItem(title="B", problem="P", technologies=["X"], outcome="O"),
                ProjectItem(title="C", problem="P", technologies=["X"], outcome="O"),
            ],
            skills=[
                SkillCategory(category="Languages", items=["Python", "SQL"]),
                SkillCategory(category="Tools", items=["Git", "Docker"]),
            ],
            career_paths=["A", "B"],
        )
        schema = build_website_schema(portfolio)
        assert classify_density(schema) == "medium"

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_density_attribute_appears_in_rendered_html(self, theme):
        schema = build_website_schema(_portfolio(), theme=theme)
        files = render(schema)
        assert 'data-density="sparse"' in files["index.html"]


# ── 2. Empty section removal ──────────────────────────────────────────────

class TestEmptySectionRemoval:
    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_no_contact_info_removes_contact_section(self, theme):
        schema = build_website_schema(_portfolio(contact=ContactInfo()), theme=theme)
        html = render(schema)["index.html"]
        assert 'id="contact"' not in html

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_no_contact_info_never_shows_fallback_message(self, theme):
        schema = build_website_schema(_portfolio(contact=ContactInfo()), theme=theme)
        html = render(schema)["index.html"]
        assert "No contact information provided" not in html

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_with_contact_info_section_is_present(self, theme):
        schema = build_website_schema(
            _portfolio(contact=ContactInfo(email="a@example.com")), theme=theme
        )
        html = render(schema)["index.html"]
        assert 'id="contact"' in html
        assert "a@example.com" in html

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_no_leftover_conditional_markers(self, theme):
        """Markers must never leak into shipped HTML regardless of branch taken."""
        for contact in (ContactInfo(), ContactInfo(email="a@example.com")):
            schema = build_website_schema(_portfolio(contact=contact), theme=theme)
            html = render(schema)["index.html"]
            assert "@if:" not in html
            assert "@endif:" not in html

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_no_contact_nav_link_dangles(self, theme):
        """When contact is removed, no nav link should still point at #contact."""
        schema = build_website_schema(_portfolio(contact=ContactInfo()), theme=theme)
        html = render(schema)["index.html"]
        assert 'href="#contact"' not in html


# ── 3. Length guards ───────────────────────────────────────────────────────

class TestLengthGuards:
    def test_truncate_short_text_unchanged(self):
        assert truncate("Short title", 60) == "Short title"

    def test_truncate_long_text_is_shortened(self):
        long_title = "A" * 100
        result = truncate(long_title, 60)
        assert len(result) <= 60
        assert result.endswith("…")

    def test_truncate_breaks_on_word_boundary(self):
        text = "AI Portfolio Generator for Job Seekers Everywhere In The World"
        result = truncate(text, 40)
        assert not result.rstrip("…").endswith(("Wor", "Everyw"))  # not chopped mid-word

    def test_cap_list_under_limit_unchanged(self):
        items, overflow = cap_list(["a", "b"], 5)
        assert items == ["a", "b"]
        assert overflow == 0

    def test_cap_list_over_limit_truncated(self):
        items, overflow = cap_list(list("abcdefghij"), 5)
        assert items == ["a", "b", "c", "d", "e"]
        assert overflow == 5

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_long_project_title_does_not_appear_unguarded(self, theme):
        long_title = "Design System Unification Across Three Product Lines for a 40-Person Engineering Org"
        schema = build_website_schema(
            _portfolio(projects=[ProjectItem(title=long_title, problem="P", technologies=["X"], outcome="O")]),
            theme=theme,
        )
        html = render(schema)["index.html"]
        # The full title must never appear as a single unbroken run of visible
        # text — it's fine in a `title="..."` attribute (full text preserved
        # for accessibility), but the rendered heading text itself must be
        # capped short of the full string.
        assert "…" in html or "Person Engineering Org" not in html.split('title="')[0]

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_many_technologies_capped_with_overflow_indicator(self, theme):
        many_tech = [f"Tech{i}" for i in range(15)]
        schema = build_website_schema(
            _portfolio(projects=[ProjectItem(title="X", problem="P", technologies=many_tech, outcome="O")]),
            theme=theme,
        )
        html = render(schema)["index.html"]
        assert "more" in html.lower()

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_many_skills_in_one_category_capped(self, theme):
        many_skills = [f"Skill{i}" for i in range(20)]
        schema = build_website_schema(
            _portfolio(skills=[SkillCategory(category="Tools", items=many_skills)]),
            theme=theme,
        )
        html = render(schema)["index.html"]
        assert "more" in html.lower()


# ── 4 & 5. Adaptive spacing / hero sizing hooks ────────────────────────────

class TestAdaptiveSpacingAndHeroSizing:
    def test_name_size_class_long_name(self):
        assert name_size_class("Ananya Krishnamurthy Rao") == "name-long"

    def test_name_size_class_short_name(self):
        assert name_size_class("Sam Lee") == ""

    def test_headline_size_class_long_headline(self):
        long_headline = "A" * 100
        assert headline_size_class(long_headline) == "headline-long"

    def test_headline_size_class_short_headline(self):
        assert headline_size_class("Short.") == ""

    @pytest.mark.parametrize("theme", [TemplateTheme.MINIMAL, TemplateTheme.EXECUTIVE, TemplateTheme.DEVELOPER, TemplateTheme.CREATIVE])
    def test_long_name_gets_size_class_in_html(self, theme):
        """Excludes modern-saas: its hero leads with the headline, not the
        candidate's name (the name only appears small in the navbar), so
        there's no overflow risk there to guard against."""
        schema = build_website_schema(
            _portfolio(hero=HeroSection(name="Ananya Krishnamurthy Rao", role="Engineer", headline="Hi.")),
            theme=theme,
        )
        html = render(schema)["index.html"]
        assert "name-long" in html

    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_density_spacing_variables_defined_in_css(self, theme):
        css = (TEMPLATES_DIR / theme.value / "styles.css").read_text(encoding="utf-8")
        assert 'data-density="sparse"' in css
        assert 'data-density="dense"' in css


# ── 6. Adaptive project rendering (flex-stretch fix) ───────────────────────

class TestAdaptiveProjectRendering:
    def test_single_project_minimal_has_no_empty_list(self):
        schema = build_website_schema(_portfolio(), theme=TemplateTheme.MINIMAL)
        html = render(schema)["index.html"]
        assert "project-list" not in html  # only the spotlight renders

    def test_creative_career_card_cannot_stretch_full_width(self):
        """Regression test for the single-item flex-stretch bug found in the
        design audit: a lone career card used to fill 100% of the row."""
        css = (TEMPLATES_DIR / "creative-portfolio" / "styles.css").read_text(encoding="utf-8")
        assert "flex: 1 1 220px" not in css
        assert "max-width" in css.split(".creative-career-card {")[1].split("}")[0]


# ── Mobile navigation works (not just hidden) ──────────────────────────────

_THEMES_WITH_HAMBURGER = [
    TemplateTheme.MINIMAL, TemplateTheme.EXECUTIVE, TemplateTheme.CREATIVE, TemplateTheme.SAAS,
]


class TestMobileNavigation:
    @pytest.mark.parametrize("theme", _THEMES_WITH_HAMBURGER)
    def test_mobile_nav_toggle_button_exists(self, theme):
        html = (TEMPLATES_DIR / theme.value / "index.html").read_text(encoding="utf-8")
        assert "mobile-nav-toggle" in html

    def test_developer_dark_uses_tab_bar_instead_of_hamburger(self):
        """developer-dark deliberately reuses its existing tab bar as the
        mobile nav surface (made functional, see below) rather than adding
        a redundant hamburger — it has no separate mobile-nav-toggle."""
        html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
        assert "mobile-nav-toggle" not in html

    @pytest.mark.parametrize("theme", _THEMES_WITH_HAMBURGER)
    def test_mobile_nav_links_are_real_anchors_not_decorative_spans(self, theme):
        html = (TEMPLATES_DIR / theme.value / "index.html").read_text(encoding="utf-8")
        drawer = html.split('id="mobile-nav-drawer"')[1].split("</div>")[0]
        assert 'aria-hidden="true"' not in drawer
        assert "<a " in drawer

    def test_developer_dark_tab_bar_is_now_functional(self):
        """The tab bar used to be aria-hidden spans with no href — the one
        and only mobile nav element doing nothing when tapped."""
        html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
        tab_bar_section = html.split('class="tab-bar"')[1].split("</nav>")[0]
        assert "<a " in tab_bar_section
        assert 'href="#about"' in tab_bar_section
        assert 'aria-hidden="true"' not in html.split('class="tab-bar"')[0][-200:]

    @pytest.mark.parametrize("theme", _THEMES_WITH_HAMBURGER)
    def test_mobile_nav_has_javascript_wiring(self, theme):
        html = (TEMPLATES_DIR / theme.value / "index.html").read_text(encoding="utf-8")
        assert "mobile-nav-toggle" in html and "addEventListener" in html


# ── Accessibility: contrast + heading semantics ────────────────────────────

class TestAccessibilityFixes:
    @staticmethod
    def _contrast(fg: str, bg: str) -> float:
        def lum(hexcolor: str) -> float:
            hexcolor = hexcolor.lstrip("#")
            r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (0, 2, 4))
            def adj(c: float) -> float:
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = adj(r), adj(g), adj(b)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        l1, l2 = lum(fg) + 0.05, lum(bg) + 0.05
        return max(l1, l2) / min(l1, l2)

    @pytest.mark.parametrize(
        "theme,fg,bg",
        [
            ("minimal-white-orange", "767676", "ffffff"),
            ("developer-dark", "7d8590", "0d1117"),
            ("modern-saas", "6b7785", "ffffff"),
            ("executive-black-gold", "948e7e", "0b0b0c"),
        ],
    )
    def test_text_faint_passes_aa_contrast(self, theme, fg, bg):
        ratio = self._contrast(fg, bg)
        assert ratio >= 4.5, f"{theme} text-faint contrast {ratio:.2f}:1 fails WCAG AA"

    def test_developer_dark_has_h1_for_name(self):
        html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
        assert "<h1" in html

    def test_developer_dark_has_h2_for_sections(self):
        html = (TEMPLATES_DIR / "developer-dark" / "index.html").read_text(encoding="utf-8")
        assert html.count("<h2") >= 4  # About, Skills, Experience, Projects (Contact conditional)
