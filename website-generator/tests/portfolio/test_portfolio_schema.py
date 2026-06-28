"""Unit tests for src/portfolio/portfolio_schema.py.

Tests instantiation, defaults, field types, and model_dump output.
No network calls. No Ollama.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.portfolio.portfolio_schema import (
    PORTFOLIO_SCHEMA_VERSION,
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)


# ── HeroSection ───────────────────────────────────────────────────────────────

def test_hero_section_instantiates():
    hero = HeroSection(name="Pawan", role="ML Engineer", headline="Building the future.")
    assert hero.name == "Pawan"
    assert hero.role == "ML Engineer"
    assert hero.headline == "Building the future."


def test_hero_section_defaults_to_empty_strings():
    hero = HeroSection()
    assert hero.name == ""
    assert hero.role == ""
    assert hero.headline == ""


# ── ContactInfo ───────────────────────────────────────────────────────────────

def test_contact_info_all_none_by_default():
    contact = ContactInfo()
    assert contact.email is None
    assert contact.phone is None
    assert contact.location is None
    assert contact.linkedin is None


def test_contact_info_stores_values():
    contact = ContactInfo(
        email="pawan@example.com",
        phone="+91-9876543210",
        location="Delhi, India",
        linkedin="linkedin.com/in/pawan",
    )
    assert contact.email == "pawan@example.com"
    assert contact.linkedin == "linkedin.com/in/pawan"


# ── ProjectItem ──────────────────────────────────────────────────────────────

def test_project_item_instantiates_with_all_fields():
    p = ProjectItem(
        title="AI Portfolio Generator",
        problem="Resumes are static and hard to showcase online.",
        technologies=["Python", "Ollama"],
        outcome="Generates a deployable site from a PDF.",
        github_url="https://github.com/example/repo",
        demo_url="https://example.com",
    )
    assert p.title == "AI Portfolio Generator"
    assert p.technologies == ["Python", "Ollama"]
    assert p.github_url == "https://github.com/example/repo"


def test_project_item_defaults():
    p = ProjectItem()
    assert p.title == ""
    assert p.problem == ""
    assert p.technologies == []
    assert p.outcome == ""
    assert p.github_url is None
    assert p.demo_url is None


# ── SkillCategory ────────────────────────────────────────────────────────────

def test_skill_category_instantiates():
    c = SkillCategory(category="Programming Languages", items=["Python", "Go"])
    assert c.category == "Programming Languages"
    assert c.items == ["Python", "Go"]


def test_skill_category_defaults():
    c = SkillCategory()
    assert c.category == ""
    assert c.items == []


# ── PortfolioSchema ───────────────────────────────────────────────────────────

def _make_valid_portfolio(**overrides) -> PortfolioSchema:
    defaults = dict(
        hero=HeroSection(name="Pawan", role="ML Engineer", headline="Headline here."),
        about="Pawan is an ML engineer.",
        skills=[SkillCategory(category="Programming Languages", items=["Python"])],
        projects=[
            ProjectItem(
                title="Build an AI app",
                problem="Problem statement.",
                technologies=["Python"],
                outcome="Outcome statement.",
            )
        ],
        career_paths=["ML Engineer"],
        contact=ContactInfo(email="pawan@example.com"),
    )
    defaults.update(overrides)
    return PortfolioSchema(**defaults)


def test_portfolio_schema_instantiates():
    p = _make_valid_portfolio()
    assert isinstance(p, PortfolioSchema)


def test_portfolio_schema_version_is_set():
    p = _make_valid_portfolio()
    assert p.schema_version == PORTFOLIO_SCHEMA_VERSION


def test_portfolio_generated_at_is_datetime():
    p = _make_valid_portfolio()
    assert isinstance(p.generated_at, datetime)


def test_portfolio_llm_model_default_is_empty():
    p = _make_valid_portfolio()
    assert p.llm_model == ""


def test_portfolio_llm_model_stored_when_set():
    p = _make_valid_portfolio(llm_model="qwen3:14b")
    assert p.llm_model == "qwen3:14b"


def test_portfolio_hero_is_hero_section():
    p = _make_valid_portfolio()
    assert isinstance(p.hero, HeroSection)


def test_portfolio_contact_is_contact_info():
    p = _make_valid_portfolio()
    assert isinstance(p.contact, ContactInfo)


def test_portfolio_skills_is_list_of_skill_category():
    p = _make_valid_portfolio(
        skills=[
            SkillCategory(category="Programming Languages", items=["Python"]),
            SkillCategory(category="Tools", items=["Docker", "Git"]),
        ]
    )
    assert isinstance(p.skills, list)
    assert all(isinstance(s, SkillCategory) for s in p.skills)
    assert p.skills[1].items == ["Docker", "Git"]


def test_portfolio_projects_is_list_of_project_item():
    p = _make_valid_portfolio(
        projects=[
            ProjectItem(title="Project A", problem="P", technologies=[], outcome="O"),
            ProjectItem(title="Project B", problem="P", technologies=[], outcome="O"),
        ]
    )
    assert isinstance(p.projects, list)
    assert all(isinstance(proj, ProjectItem) for proj in p.projects)
    assert p.projects[0].title == "Project A"


def test_portfolio_career_paths_is_list_of_str():
    p = _make_valid_portfolio(career_paths=["ML Engineer", "Backend Dev"])
    assert isinstance(p.career_paths, list)
    assert all(isinstance(c, str) for c in p.career_paths)


def test_portfolio_model_dump_contains_all_keys():
    p = _make_valid_portfolio()
    dumped = p.model_dump()
    assert "hero" in dumped
    assert "about" in dumped
    assert "skills" in dumped
    assert "projects" in dumped
    assert "career_paths" in dumped
    assert "contact" in dumped
    assert "schema_version" in dumped
    assert "generated_at" in dumped
    assert "llm_model" in dumped


def test_portfolio_model_dump_hero_is_dict():
    p = _make_valid_portfolio()
    dumped = p.model_dump()
    assert isinstance(dumped["hero"], dict)
    assert "name" in dumped["hero"]
    assert "role" in dumped["hero"]
    assert "headline" in dumped["hero"]


def test_portfolio_model_dump_projects_are_dicts_with_structured_fields():
    p = _make_valid_portfolio()
    dumped = p.model_dump()
    assert isinstance(dumped["projects"][0], dict)
    for key in ("title", "problem", "technologies", "outcome", "github_url", "demo_url"):
        assert key in dumped["projects"][0]


def test_portfolio_model_dump_skills_are_dicts_with_category_and_items():
    p = _make_valid_portfolio()
    dumped = p.model_dump()
    assert isinstance(dumped["skills"][0], dict)
    assert "category" in dumped["skills"][0]
    assert "items" in dumped["skills"][0]


def test_portfolio_model_dump_json_mode_serialises_datetime():
    p = _make_valid_portfolio()
    dumped = p.model_dump(mode="json")
    # datetime should be a string in JSON mode
    assert isinstance(dumped["generated_at"], str)
