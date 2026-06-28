"""Unit tests for src/portfolio/portfolio_validator.py.

Tests every validation rule — valid schema passes, each invalid field raises
PortfolioValidationError with a meaningful message.
No network calls. No Ollama.
"""

from __future__ import annotations

import pytest

from src.portfolio.exceptions import PortfolioValidationError
from src.portfolio.portfolio_schema import (
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)
from src.portfolio.portfolio_validator import validate


# ── Shared helper ─────────────────────────────────────────────────────────────

def _project(**overrides) -> ProjectItem:
    defaults = dict(
        title="Build an AI app",
        problem="A problem statement.",
        technologies=["Python"],
        outcome="An outcome statement.",
    )
    defaults.update(overrides)
    return ProjectItem(**defaults)


def _make_valid_portfolio(**overrides) -> PortfolioSchema:
    defaults = dict(
        hero=HeroSection(name="Pawan", role="ML Engineer", headline="Headline."),
        about="A professional bio.",
        skills=[SkillCategory(category="Programming Languages", items=["Python", "ML"])],
        projects=[_project()],
        career_paths=["ML Engineer"],
        contact=ContactInfo(email="pawan@example.com"),
    )
    defaults.update(overrides)
    return PortfolioSchema(**defaults)


# ── Happy path ────────────────────────────────────────────────────────────────

def test_valid_portfolio_passes_validation():
    """A fully populated, valid portfolio raises nothing."""
    validate(_make_valid_portfolio())


def test_valid_portfolio_with_multiple_items_passes():
    p = _make_valid_portfolio(
        skills=[
            SkillCategory(category="Programming Languages", items=["Python", "Go"]),
            SkillCategory(category="Tools", items=["Docker", "Git"]),
        ],
        projects=[_project(title="Project A"), _project(title="Project B"), _project(title="Project C")],
        career_paths=["ML Engineer", "Backend Dev", "AI Developer"],
    )
    validate(p)


def test_valid_portfolio_with_no_contact_details_passes():
    """Contact fields are all optional — empty ContactInfo is still valid."""
    p = _make_valid_portfolio(contact=ContactInfo())
    validate(p)


def test_valid_portfolio_project_with_no_technologies_passes():
    """technologies is allowed to be an empty list."""
    p = _make_valid_portfolio(projects=[_project(technologies=[])])
    validate(p)


# ── Hero validation ───────────────────────────────────────────────────────────

def test_empty_hero_name_raises():
    p = _make_valid_portfolio(
        hero=HeroSection(name="", role="ML Engineer", headline="Headline.")
    )
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "hero.name" in str(exc_info.value)


def test_whitespace_hero_name_raises():
    p = _make_valid_portfolio(
        hero=HeroSection(name="   ", role="ML Engineer", headline="Headline.")
    )
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "hero.name" in str(exc_info.value)


def test_empty_hero_role_raises():
    p = _make_valid_portfolio(
        hero=HeroSection(name="Pawan", role="", headline="Headline.")
    )
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "hero.role" in str(exc_info.value)


def test_empty_hero_headline_raises():
    p = _make_valid_portfolio(
        hero=HeroSection(name="Pawan", role="ML Engineer", headline="")
    )
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "hero.headline" in str(exc_info.value)


# ── About validation ──────────────────────────────────────────────────────────

def test_empty_about_raises():
    p = _make_valid_portfolio(about="")
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "about" in str(exc_info.value)


def test_whitespace_about_raises():
    p = _make_valid_portfolio(about="   \n  ")
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "about" in str(exc_info.value)


# ── Skills validation ─────────────────────────────────────────────────────────

def test_empty_skills_list_raises():
    p = _make_valid_portfolio(skills=[])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "skills" in str(exc_info.value)


def test_skill_category_empty_name_raises():
    p = _make_valid_portfolio(skills=[SkillCategory(category="", items=["Python"])])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "skills[0].category" in str(exc_info.value)


def test_skill_category_empty_items_raises():
    p = _make_valid_portfolio(skills=[SkillCategory(category="Tools", items=[])])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "skills[0].items" in str(exc_info.value)


def test_skill_item_whitespace_string_raises():
    p = _make_valid_portfolio(
        skills=[SkillCategory(category="Tools", items=["  ", "Python"])]
    )
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "skills[0].items[0]" in str(exc_info.value)


# ── Projects validation ───────────────────────────────────────────────────────

def test_empty_projects_list_raises():
    p = _make_valid_portfolio(projects=[])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "projects" in str(exc_info.value)


def test_project_empty_title_raises():
    p = _make_valid_portfolio(projects=[_project(title="")])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "projects[0].title" in str(exc_info.value)


def test_project_empty_problem_raises():
    p = _make_valid_portfolio(projects=[_project(problem="")])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "projects[0].problem" in str(exc_info.value)


def test_project_empty_outcome_raises():
    p = _make_valid_portfolio(projects=[_project(outcome="")])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "projects[0].outcome" in str(exc_info.value)


def test_project_blank_technology_raises():
    p = _make_valid_portfolio(projects=[_project(technologies=["Python", "  "])])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "projects[0].technologies[1]" in str(exc_info.value)


# ── Career paths validation ───────────────────────────────────────────────────

def test_empty_career_paths_list_raises():
    p = _make_valid_portfolio(career_paths=[])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "career_paths" in str(exc_info.value)


def test_career_path_empty_string_raises():
    p = _make_valid_portfolio(career_paths=["ML Engineer", ""])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert "career_paths[1]" in str(exc_info.value)


# ── Error message quality ─────────────────────────────────────────────────────

def test_validation_error_has_field_attribute():
    p = _make_valid_portfolio(about="")
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert exc_info.value.field == "about"


def test_validation_error_has_reason_attribute():
    p = _make_valid_portfolio(about="")
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    assert exc_info.value.reason


def test_validation_error_str_includes_field_and_reason():
    p = _make_valid_portfolio(skills=[])
    with pytest.raises(PortfolioValidationError) as exc_info:
        validate(p)
    msg = str(exc_info.value)
    assert "skills" in msg
    assert "at least one" in msg
