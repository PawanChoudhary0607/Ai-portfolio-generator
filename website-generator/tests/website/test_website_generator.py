"""Unit tests for src/website/website_generator.py.

Tests schema building, HTML rendering, file output, and helper functions.
No network calls. No Ollama. Uses tmp_path for file I/O.

Theme-specific *layout* assertions (e.g. "developer-dark uses a code-block
for skills") live in test_website_templates.py / test_theme_renderers.py —
this file focuses on the theme-agnostic generation pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.portfolio.portfolio_schema import (
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)
from src.website.exceptions import WebsiteGenerationError
from src.website.render_utils import build_initials, escape
from src.website.website_generator import (
    build_website_schema,
    generate,
    generate_from_json,
    render,
)
from src.website.website_schema import TemplateTheme

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "valid_portfolio.json"


def _make_portfolio(**overrides) -> PortfolioSchema:
    defaults = dict(
        llm_model="qwen3:14b",
        hero=HeroSection(
            name="Pawan Choudhary",
            role="Python & ML Engineer",
            headline="Building intelligent systems.",
        ),
        about="Pawan is an AI/ML engineer.",
        skills=[
            SkillCategory(category="Programming Languages", items=["Python"]),
            SkillCategory(category="Frameworks", items=["FastAPI"]),
            SkillCategory(category="Tools", items=["Docker"]),
        ],
        projects=[
            ProjectItem(
                title="AI Portfolio Generator",
                problem="Resumes are static and hard to showcase online.",
                technologies=["Python", "Ollama"],
                outcome="Converts PDFs to portfolio sites.",
            ),
            ProjectItem(
                title="FastAPI Microservice",
                problem="Needed a deployable REST API.",
                technologies=["FastAPI", "Docker"],
                outcome="Containerised REST API.",
            ),
        ],
        career_paths=["ML Engineer", "Backend Developer"],
        contact=ContactInfo(
            email="pawan@example.com",
            phone="+91-9876543210",
            location="Delhi, India",
            linkedin="linkedin.com/in/pawan",
        ),
    )
    defaults.update(overrides)
    return PortfolioSchema(**defaults)


# ── render_utils helper tests ───────────────────────────────────────────────────

class TestBuildInitials:
    def test_two_word_name(self):
        assert build_initials("Pawan Choudhary") == "PC"

    def test_single_word_name(self):
        assert build_initials("Madonna") == "M"

    def test_three_word_name(self):
        assert build_initials("Mary Jane Watson") == "MW"

    def test_empty_string(self):
        assert build_initials("") == "?"

    def test_lowercase_name(self):
        assert build_initials("john doe") == "JD"

    def test_whitespace_only(self):
        assert build_initials("   ") == "?"


class TestEscape:
    def test_ampersand(self):
        assert escape("A&B") == "A&amp;B"

    def test_angle_brackets(self):
        assert escape("<script>") == "&lt;script&gt;"

    def test_double_quotes(self):
        assert escape('"hello"') == "&quot;hello&quot;"

    def test_no_special_chars(self):
        assert escape("Hello World") == "Hello World"

    def test_combined(self):
        result = escape('<a href="x&y">')
        assert "&lt;" in result
        assert "&amp;" in result
        assert "&quot;" in result


# ── build_website_schema tests ─────────────────────────────────────────────────

class TestBuildWebsiteSchema:
    def test_hero_fields_copied(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert schema.hero.name == "Pawan Choudhary"
        assert schema.hero.role == "Python & ML Engineer"
        assert schema.hero.initials == "PC"

    def test_about_copied(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert schema.about.bio == "Pawan is an AI/ML engineer."

    def test_skills_categories_copied(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert len(schema.skills.categories) == 3
        flat = [item for c in schema.skills.categories for item in c.items]
        assert "Python" in flat

    def test_projects_transformed(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert len(schema.projects.items) == 2
        assert schema.projects.items[0].index == 1
        assert schema.projects.items[0].title == "AI Portfolio Generator"
        assert schema.projects.items[0].technologies == ["Python", "Ollama"]

    def test_first_project_is_featured(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert schema.projects.items[0].is_featured is True
        assert schema.projects.items[1].is_featured is False

    def test_career_paths_transformed(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert len(schema.career_paths.items) == 2
        assert schema.career_paths.items[0].title == "ML Engineer"

    def test_contact_copied(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert schema.contact.email == "pawan@example.com"
        assert schema.contact.has_contact_info is True

    def test_contact_has_info_false_when_all_none(self):
        portfolio = _make_portfolio(contact=ContactInfo())
        schema = build_website_schema(portfolio)
        assert schema.contact.has_contact_info is False

    def test_page_title_includes_name(self):
        portfolio = _make_portfolio()
        schema = build_website_schema(portfolio)
        assert "Pawan Choudhary" in schema.page_title

    def test_theme_default_is_minimal(self):
        schema = build_website_schema(_make_portfolio())
        assert schema.theme == TemplateTheme.MINIMAL

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_theme_applied(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        assert schema.theme == theme

    def test_llm_model_forwarded(self):
        schema = build_website_schema(_make_portfolio())
        assert schema.llm_model == "qwen3:14b"

    def test_empty_name_gives_fallback_initials(self):
        portfolio = _make_portfolio(hero=HeroSection(name="", role="Dev", headline="Hello"))
        schema = build_website_schema(portfolio)
        assert schema.hero.initials == "?"


# ── render tests ───────────────────────────────────────────────────────────────

class TestRender:
    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_render_produces_three_files(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert set(files.keys()) == {"index.html", "styles.css", "portfolio_data.json"}

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_html_contains_hero_name(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert "Pawan Choudhary" in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_html_contains_skills(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert "Python" in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_html_contains_project_technologies(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert "Ollama" in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_html_has_no_unfilled_placeholders(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert "{{" not in files["index.html"]
        assert "}}" not in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_css_is_non_empty(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert len(files["styles.css"]) > 100

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_contact_email_rendered(self, theme):
        schema = build_website_schema(_make_portfolio(), theme=theme)
        files = render(schema)
        assert "pawan@example.com" in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_no_contact_info_does_not_crash(self, theme):
        portfolio = _make_portfolio(contact=ContactInfo())
        schema = build_website_schema(portfolio, theme=theme)
        files = render(schema)
        assert "{{" not in files["index.html"]

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_project_with_links_renders_anchors(self, theme):
        portfolio = _make_portfolio(
            projects=[
                ProjectItem(
                    title="Linked Project",
                    problem="P",
                    technologies=["Python"],
                    outcome="O",
                    github_url="https://github.com/example/repo",
                    demo_url="https://example.com",
                )
            ]
        )
        schema = build_website_schema(portfolio, theme=theme)
        files = render(schema)
        assert "https://github.com/example/repo" in files["index.html"]
        assert "https://example.com" in files["index.html"]

    def test_portfolio_data_json_is_valid(self):
        schema = build_website_schema(_make_portfolio())
        files = render(schema)
        data = json.loads(files["portfolio_data.json"])
        assert data["hero"]["name"] == "Pawan Choudhary"
        assert "skills" in data
        assert "projects" in data

    def test_html_escaped_special_chars(self):
        portfolio = _make_portfolio(
            hero=HeroSection(name="Dev & Co", role="R&D", headline="Hello <world>")
        )
        schema = build_website_schema(portfolio)
        files = render(schema)
        html = files["index.html"]
        assert "&amp;" in html
        assert "&lt;" in html

    def test_invalid_theme_dir_raises(self):
        from unittest.mock import patch
        from src.website.website_generator import _get_template_dir
        with patch("src.website.website_generator.TEMPLATES_DIR", Path("/nonexistent")):
            with pytest.raises(WebsiteGenerationError, match="template directory not found"):
                _get_template_dir(TemplateTheme.MINIMAL)


# ── generate tests (file I/O) ──────────────────────────────────────────────────

class TestGenerate:
    def test_generates_three_files(self, tmp_path):
        portfolio = _make_portfolio()
        site_dir = generate(portfolio, output_dir=tmp_path / "site")
        files = {f.name for f in site_dir.iterdir()}
        assert files == {"index.html", "styles.css", "portfolio_data.json"}

    def test_output_dir_created(self, tmp_path):
        portfolio = _make_portfolio()
        out = tmp_path / "deep" / "nested" / "site"
        site_dir = generate(portfolio, output_dir=out)
        assert site_dir.is_dir()

    def test_returns_resolved_path(self, tmp_path):
        portfolio = _make_portfolio()
        site_dir = generate(portfolio, output_dir=tmp_path / "site")
        assert site_dir.is_absolute()

    def test_index_html_content(self, tmp_path):
        portfolio = _make_portfolio()
        site_dir = generate(portfolio, output_dir=tmp_path / "site")
        html = (site_dir / "index.html").read_text(encoding="utf-8")
        assert "Pawan Choudhary" in html
        assert "Python" in html

    def test_portfolio_data_json_content(self, tmp_path):
        portfolio = _make_portfolio()
        site_dir = generate(portfolio, output_dir=tmp_path / "site")
        data = json.loads((site_dir / "portfolio_data.json").read_text())
        assert data["hero"]["name"] == "Pawan Choudhary"

    @pytest.mark.parametrize("theme", list(TemplateTheme))
    def test_all_themes_generate_successfully(self, theme, tmp_path):
        portfolio = _make_portfolio()
        site_dir = generate(portfolio, output_dir=tmp_path / theme.value, theme=theme)
        assert (site_dir / "index.html").exists()
        assert (site_dir / "styles.css").exists()
        html = (site_dir / "index.html").read_text(encoding="utf-8")
        assert "{{" not in html


# ── generate_from_json tests ───────────────────────────────────────────────────

class TestGenerateFromJson:
    def test_loads_fixture_json(self, tmp_path):
        site_dir = generate_from_json(portfolio_json_path=FIXTURE_JSON, output_dir=tmp_path / "site")
        assert (site_dir / "index.html").exists()

    def test_html_contains_fixture_name(self, tmp_path):
        site_dir = generate_from_json(portfolio_json_path=FIXTURE_JSON, output_dir=tmp_path / "site")
        html = (site_dir / "index.html").read_text(encoding="utf-8")
        assert "Pawan Choudhary" in html

    def test_invalid_json_raises(self, tmp_path):
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json", encoding="utf-8")
        with pytest.raises(WebsiteGenerationError, match="cannot load portfolio JSON"):
            generate_from_json(portfolio_json_path=bad_json, output_dir=tmp_path / "out")

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(WebsiteGenerationError, match="cannot load portfolio JSON"):
            generate_from_json(portfolio_json_path=tmp_path / "nonexistent.json", output_dir=tmp_path / "out")

    def test_default_output_dir_derived_from_stem(self, tmp_path):
        import shutil
        dest = tmp_path / "myresume_portfolio.json"
        shutil.copy(FIXTURE_JSON, dest)
        from unittest.mock import patch
        with patch("src.website.website_generator.DEFAULT_OUTPUT_BASE", tmp_path / "output"):
            site_dir = generate_from_json(portfolio_json_path=dest)
        assert "myresume" in site_dir.name
        assert "site" in site_dir.name
