"""Unit tests for src/website/theme_renderers.py.

Each public render_*() function is exercised against every theme to confirm
dispatch works, and against theme-specific cases to confirm the structural
differences the redesign was built around (e.g. developer-dark emits a
code-block, executive-black-gold emits numbered serif blocks).
"""

from __future__ import annotations

import pytest

from src.website import theme_renderers as tr
from src.website.website_schema import (
    CareerPathContent,
    ContactContent,
    HeroContent,
    ProjectContent,
    SkillCategoryContent,
    TemplateTheme,
)

ALL_THEMES = list(TemplateTheme)


def _categories():
    return [
        SkillCategoryContent(category="Programming Languages", items=["Python", "SQL"]),
        SkillCategoryContent(category="Tools", items=["Docker"]),
    ]


def _projects():
    return [
        ProjectContent(
            title="AI Portfolio Generator",
            problem="Resumes are static.",
            technologies=["Python", "Ollama"],
            outcome="Generates a deployable site.",
            index=1,
            is_featured=True,
        ),
        ProjectContent(
            title="FastAPI Service",
            problem="Needed a deployable API.",
            technologies=["FastAPI"],
            outcome="Shipped a working microservice.",
            github_url="https://github.com/example/repo",
            demo_url="https://example.com",
            index=2,
        ),
    ]


def _careers():
    return [
        CareerPathContent(title="ML Engineer", index=1),
        CareerPathContent(title="Backend Developer", index=2),
    ]


def _contact_full():
    return ContactContent(
        email="pawan@example.com",
        phone="+91-9876543210",
        location="Delhi, India",
        linkedin="linkedin.com/in/pawan",
        has_contact_info=True,
    )


def _contact_empty():
    return ContactContent(has_contact_info=False)


def _hero():
    return HeroContent(name="Pawan Choudhary", role="ML Engineer", headline="Building things.", initials="PC")


# ── Dispatch works for every theme without raising ─────────────────────────────

@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_skills_does_not_raise(theme):
    out = tr.render_skills(theme, _categories())
    assert "Python" in out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_projects_does_not_raise(theme):
    out = tr.render_projects(theme, _projects())
    assert "AI Portfolio Generator" in out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_career_does_not_raise(theme):
    out = tr.render_career(theme, _careers())
    assert "ML Engineer" in out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_contact_full_does_not_raise(theme):
    out = tr.render_contact(theme, _contact_full())
    assert "pawan@example.com" in out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_contact_empty_does_not_raise(theme):
    out = tr.render_contact(theme, _contact_empty())
    assert out  # always returns *something*, even if just a fallback message


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_social_handles_no_contact(theme):
    out = tr.render_social(theme, _contact_empty())
    assert out == "" or isinstance(out, str)


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_social_includes_email_when_present(theme):
    out = tr.render_social(theme, _contact_full())
    assert "pawan@example.com" in out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_render_hero_extra_does_not_raise(theme):
    # Should never raise regardless of whether the theme uses this hook.
    tr.render_hero_extra(theme, _hero(), _contact_full())


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_empty_projects_list_does_not_raise(theme):
    out = tr.render_projects(theme, [])
    assert out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_empty_skills_list_does_not_raise(theme):
    out = tr.render_skills(theme, [])
    assert out


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_empty_career_list_does_not_raise(theme):
    out = tr.render_career(theme, [])
    assert out


# ── Project link placeholders: every theme must reserve the slot ──────────────

@pytest.mark.parametrize("theme", ALL_THEMES)
def test_project_without_links_does_not_render_broken_anchor(theme):
    project_no_links = [
        ProjectContent(title="No Links", problem="P", technologies=["X"], outcome="O", index=1)
    ]
    out = tr.render_projects(theme, project_no_links)
    assert 'href=""' not in out
    assert "href='None'" not in out
    assert "None" not in out  # github_url/demo_url=None must never leak as text


@pytest.mark.parametrize("theme", ALL_THEMES)
def test_project_with_links_renders_both_urls(theme):
    out = tr.render_projects(theme, _projects())
    assert "https://github.com/example/repo" in out
    assert "https://example.com" in out


# ── Theme-specific structural assertions ────────────────────────────────────────

def test_minimal_skills_render_pill_badges():
    out = tr.render_skills(TemplateTheme.MINIMAL, _categories())
    assert "skill-badge" in out
    assert "skill-group-label" in out


def test_minimal_projects_render_spotlight_and_rows():
    out = tr.render_projects(TemplateTheme.MINIMAL, _projects())
    assert "project-spotlight" in out
    assert "project-row" in out


def test_executive_skills_render_inline_dot_separated_list():
    out = tr.render_skills(TemplateTheme.EXECUTIVE, _categories())
    assert "exec-skill-row" in out
    assert "&middot;" in out


def test_executive_projects_render_numbered_blocks_with_pull_quote():
    out = tr.render_projects(TemplateTheme.EXECUTIVE, _projects())
    assert "exec-numeral" in out
    assert "exec-outcome" in out


def test_executive_career_has_no_timeline_dots():
    """Executive theme deliberately uses a numbered list, not the sidebar
    theme's timeline-with-dots pattern."""
    out = tr.render_career(TemplateTheme.EXECUTIVE, _careers())
    assert "timeline-marker" not in out
    assert "exec-path" in out


def test_developer_skills_render_as_json_block():
    out = tr.render_skills(TemplateTheme.DEVELOPER, _categories())
    assert "tok-key" in out
    assert "tok-string" in out
    assert '"programming_languages"' in out.lower()


def test_developer_projects_render_as_function_blocks():
    out = tr.render_projects(TemplateTheme.DEVELOPER, _projects())
    assert "function" in out
    assert "tok-comment" in out


def test_developer_career_renders_as_commit_log():
    out = tr.render_career(TemplateTheme.DEVELOPER, _careers())
    assert "commit-hash" in out
    assert "commit-msg" in out


def test_developer_contact_renders_as_env_file():
    out = tr.render_contact(TemplateTheme.DEVELOPER, _contact_full())
    assert "tok-key" in out
    assert "EMAIL" in out


def test_creative_skills_render_as_tiles():
    out = tr.render_skills(TemplateTheme.CREATIVE, _categories())
    assert "skill-tile" in out


def test_creative_projects_render_with_watermark_numerals():
    out = tr.render_projects(TemplateTheme.CREATIVE, _projects())
    assert "creative-watermark" in out


def test_creative_career_alternates_rotation_classes():
    out = tr.render_career(TemplateTheme.CREATIVE, _careers())
    assert "rotate-l" in out
    assert "rotate-r" in out


def test_saas_skills_render_as_feature_cards():
    out = tr.render_skills(TemplateTheme.SAAS, _categories())
    assert "saas-feature-card" in out
    assert "saas-feature-icon" in out


def test_saas_projects_render_as_case_studies():
    out = tr.render_projects(TemplateTheme.SAAS, _projects())
    assert "saas-case" in out
    assert "Case Study" in out


def test_saas_projects_alternate_flip_class():
    out = tr.render_projects(TemplateTheme.SAAS, _projects())
    assert "saas-case-flip" in out  # second project (index 1, odd) should flip


def test_saas_career_renders_as_numbered_steps():
    out = tr.render_career(TemplateTheme.SAAS, _careers())
    assert "saas-step-circle" in out


def test_saas_stats_row_counts_are_correct():
    out = tr.render_saas_stats_row(skill_count=4, project_count=3, path_count=2)
    assert ">4<" in out
    assert ">3<" in out
    assert ">2<" in out
    assert "Skill Areas" in out
    assert "Featured Projects" in out
    assert "Career Paths" in out


# ── HTML escaping is preserved through every theme's renderer ──────────────────

@pytest.mark.parametrize("theme", ALL_THEMES)
def test_project_titles_are_escaped(theme):
    project = [ProjectContent(title="<script>alert(1)</script>", problem="P", outcome="O", index=1)]
    out = tr.render_projects(theme, project)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
