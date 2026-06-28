"""Unit tests for src/website/website_schema.py.

Tests instantiation, defaults, field types, and model_dump output.
No network calls. No file I/O.
"""

from __future__ import annotations

import pytest

from src.website.website_schema import (
    WEBSITE_SCHEMA_VERSION,
    AboutContent,
    CareerPathContent,
    CareerPathsContent,
    ContactContent,
    HeroContent,
    ProjectContent,
    ProjectsContent,
    SkillCategoryContent,
    SkillsContent,
    TemplateTheme,
    WebsiteSchema,
)


# ── TemplateTheme ──────────────────────────────────────────────────────────────

def test_template_theme_values():
    assert TemplateTheme.MINIMAL.value == "minimal-white-orange"
    assert TemplateTheme.EXECUTIVE.value == "executive-black-gold"
    assert TemplateTheme.DEVELOPER.value == "developer-dark"
    assert TemplateTheme.CREATIVE.value == "creative-portfolio"
    assert TemplateTheme.SAAS.value == "modern-saas"


def test_template_theme_from_string():
    assert TemplateTheme("minimal-white-orange") == TemplateTheme.MINIMAL
    assert TemplateTheme("executive-black-gold") == TemplateTheme.EXECUTIVE
    assert TemplateTheme("developer-dark") == TemplateTheme.DEVELOPER
    assert TemplateTheme("creative-portfolio") == TemplateTheme.CREATIVE
    assert TemplateTheme("modern-saas") == TemplateTheme.SAAS


def test_template_theme_has_exactly_five_members():
    assert len(list(TemplateTheme)) == 5


def test_template_theme_invalid_raises():
    with pytest.raises(ValueError):
        TemplateTheme("neon")


# ── HeroContent ───────────────────────────────────────────────────────────────

def test_hero_content_stores_values():
    hero = HeroContent(name="Pawan", role="ML Engineer", headline="Hello", initials="PC")
    assert hero.name == "Pawan"
    assert hero.role == "ML Engineer"
    assert hero.headline == "Hello"
    assert hero.initials == "PC"


def test_hero_content_defaults_empty():
    hero = HeroContent()
    assert hero.name == ""
    assert hero.initials == ""


# ── AboutContent ──────────────────────────────────────────────────────────────

def test_about_content_stores_bio():
    about = AboutContent(bio="A seasoned engineer.")
    assert about.bio == "A seasoned engineer."


def test_about_content_default_empty():
    about = AboutContent()
    assert about.bio == ""


# ── SkillCategoryContent / SkillsContent ──────────────────────────────────────

def test_skill_category_content_stores_values():
    cat = SkillCategoryContent(category="Programming Languages", items=["Python", "Go"])
    assert cat.category == "Programming Languages"
    assert "Python" in cat.items


def test_skills_content_stores_categories():
    skills = SkillsContent(
        categories=[SkillCategoryContent(category="Tools", items=["Docker"])]
    )
    assert len(skills.categories) == 1
    assert skills.categories[0].category == "Tools"


def test_skills_content_default_empty_list():
    skills = SkillsContent()
    assert skills.categories == []


# ── ProjectContent ────────────────────────────────────────────────────────────

def test_project_content_stores_fields():
    proj = ProjectContent(
        title="My App",
        problem="A real problem.",
        technologies=["Python"],
        outcome="A great outcome.",
        index=1,
    )
    assert proj.title == "My App"
    assert proj.problem == "A real problem."
    assert proj.technologies == ["Python"]
    assert proj.outcome == "A great outcome."
    assert proj.index == 1


def test_project_content_links_default_to_none():
    proj = ProjectContent(title="My App")
    assert proj.github_url is None
    assert proj.demo_url is None


def test_project_content_defaults():
    proj = ProjectContent()
    assert proj.title == ""
    assert proj.technologies == []
    assert proj.index == 0


# ── ProjectsContent ───────────────────────────────────────────────────────────

def test_projects_content_holds_items():
    items = [ProjectContent(title="A", index=1), ProjectContent(title="B", index=2)]
    projects = ProjectsContent(items=items)
    assert len(projects.items) == 2
    assert projects.items[0].title == "A"


def test_projects_content_default_empty():
    projects = ProjectsContent()
    assert projects.items == []


# ── CareerPathContent ─────────────────────────────────────────────────────────

def test_career_path_content_stores_fields():
    cp = CareerPathContent(title="ML Engineer", icon="🚀", index=1)
    assert cp.title == "ML Engineer"
    assert cp.icon == "🚀"


def test_career_path_content_defaults():
    cp = CareerPathContent()
    assert cp.title == ""
    assert cp.icon == "🚀"


# ── CareerPathsContent ────────────────────────────────────────────────────────

def test_career_paths_content_holds_items():
    items = [CareerPathContent(title="ML Eng", index=1)]
    cp = CareerPathsContent(items=items)
    assert len(cp.items) == 1


def test_career_paths_content_default_empty():
    cp = CareerPathsContent()
    assert cp.items == []


# ── ContactContent ────────────────────────────────────────────────────────────

def test_contact_content_stores_values():
    c = ContactContent(
        email="a@b.com",
        phone="123",
        location="Delhi",
        linkedin="li/in/x",
        has_contact_info=True,
    )
    assert c.email == "a@b.com"
    assert c.has_contact_info is True


def test_contact_content_defaults():
    c = ContactContent()
    assert c.email is None
    assert c.has_contact_info is False


# ── WebsiteSchema ─────────────────────────────────────────────────────────────

def _make_schema(**overrides) -> WebsiteSchema:
    defaults = dict(
        theme=TemplateTheme.MINIMAL,
        hero=HeroContent(name="Pawan", role="Dev", headline="Hello", initials="PC"),
        about=AboutContent(bio="Bio text."),
        skills=SkillsContent(categories=[SkillCategoryContent(category="Tools", items=["Python"])]),
        projects=ProjectsContent(items=[ProjectContent(title="P1", index=1)]),
        career_paths=CareerPathsContent(items=[CareerPathContent(title="ML Eng", index=1)]),
        contact=ContactContent(email="x@y.com", has_contact_info=True),
        page_title="Pawan — Portfolio",
        llm_model="qwen3:14b",
    )
    defaults.update(overrides)
    return WebsiteSchema(**defaults)


def test_website_schema_instantiates():
    schema = _make_schema()
    assert schema.hero.name == "Pawan"
    assert schema.theme == TemplateTheme.MINIMAL
    assert schema.schema_version == WEBSITE_SCHEMA_VERSION


def test_website_schema_version_constant():
    assert WEBSITE_SCHEMA_VERSION == "6.0"


def test_website_schema_model_dump_contains_keys():
    schema = _make_schema()
    d = schema.model_dump()
    for key in ["theme", "hero", "about", "skills", "projects", "career_paths", "contact"]:
        assert key in d, f"Missing key: {key}"


def test_website_schema_theme_serializes_as_string():
    schema = _make_schema(theme=TemplateTheme.DEVELOPER)
    d = schema.model_dump()
    assert d["theme"] == "developer-dark"


def test_website_schema_default_theme_is_modern():
    schema = _make_schema()
    assert schema.theme == TemplateTheme.MINIMAL


def test_website_schema_page_title_stored():
    schema = _make_schema(page_title="Custom Title")
    assert schema.page_title == "Custom Title"
