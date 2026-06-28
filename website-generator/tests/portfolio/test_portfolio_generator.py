"""Unit tests for src/portfolio/portfolio_generator.py.

All Ollama calls are mocked. No network dependency.
Tests cover: happy path, JSON extraction, fallback behaviour,
skill categorization, project structuring, file output, and error
propagation.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.exceptions import MalformedResponseError, OllamaUnavailableError
from src.portfolio.exceptions import PortfolioGenerationError, PortfolioValidationError
from src.portfolio.portfolio_generator import (
    _build_portfolio_prompt,
    _categorize_skills,
    _parse_portfolio_response,
    generate,
    generate_and_save,
)
from src.portfolio.portfolio_schema import PortfolioSchema, ProjectItem, SkillCategory
from src.schemas.resume import PersonalInfo, ResumeSchema

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "valid_portfolio_response.json"
VALID_RESPONSE = FIXTURE_PATH.read_text(encoding="utf-8")


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture()
def sample_resume() -> ResumeSchema:
    return ResumeSchema(
        filename="sample.pdf",
        page_count=2,
        raw_text="Pawan Choudhary\nPython, Machine Learning\nAI Portfolio Generator",
        personal=PersonalInfo(
            name="Pawan Choudhary",
            email="pawan@example.com",
            phone="+91-9876543210",
            location="Delhi, India",
            linkedin="linkedin.com/in/pawan",
        ),
        skills=["Python", "Machine Learning", "Git"],
        projects_raw="AI Portfolio Generator — local LLM pipeline",
        summary="Python developer with ML focus.",
    )


@pytest.fixture()
def sample_analysis() -> AIAnalysisSchema:
    return AIAnalysisSchema(
        strengths=["Strong Python skills", "ML experience"],
        weaknesses=["No cloud deployment"],
        missing_skills=["Docker", "CI/CD"],
        recommended_projects=["FastAPI service", "ML open-source contribution"],
        recommended_career_paths=["ML Engineer", "Backend Python Developer"],
        portfolio_sections=["About", "Skills", "Projects", "Contact"],
        summary="Pawan is an emerging AI/ML engineer with strong Python foundations.",
        llm_model="qwen3:8b",
    )


def _mock_client(response_text: str) -> MagicMock:
    mock = MagicMock()
    mock.generate.return_value = response_text
    return mock


# ── _categorize_skills() ───────────────────────────────────────────────────────

def test_categorize_skills_groups_known_keywords():
    categories = _categorize_skills(["Python", "Docker", "FastAPI", "AWS"])
    names = {c.category for c in categories}
    assert "Programming Languages" in names
    assert "Tools" in names
    assert "Frameworks" in names
    assert "Cloud" in names


def test_categorize_skills_is_case_insensitive():
    categories = _categorize_skills(["python", "DOCKER"])
    flat = {item for c in categories for item in c.items}
    assert "python" in flat
    assert "DOCKER" in flat


def test_categorize_skills_unknown_goes_to_other():
    categories = _categorize_skills(["Underwater Basket Weaving"])
    assert len(categories) == 1
    assert categories[0].category == "Other"
    assert categories[0].items == ["Underwater Basket Weaving"]


def test_categorize_skills_drops_blank_entries():
    categories = _categorize_skills(["Python", "  ", ""])
    flat = [item for c in categories for item in c.items]
    assert flat == ["Python"]


def test_categorize_skills_returns_skill_category_instances():
    categories = _categorize_skills(["Python"])
    assert all(isinstance(c, SkillCategory) for c in categories)


def test_categorize_skills_empty_list_returns_empty():
    assert _categorize_skills([]) == []


# ── _build_portfolio_prompt() ─────────────────────────────────────────────────

def test_prompt_contains_candidate_name(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "Pawan" in prompt


def test_prompt_contains_skills(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "Python" in prompt


def test_prompt_contains_system_instructions(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "JSON object" in prompt


def test_prompt_requests_structured_projects(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "technologies" in prompt
    assert "outcome" in prompt


def test_prompt_contains_analysis_summary(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "AI/ML engineer" in prompt


def test_prompt_contains_career_paths(sample_resume, sample_analysis):
    prompt = _build_portfolio_prompt(sample_resume, sample_analysis)
    assert "ML Engineer" in prompt


# ── _parse_portfolio_response() ───────────────────────────────────────────────

def test_parse_valid_response_returns_portfolio(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert isinstance(result, PortfolioSchema)


def test_parse_sets_hero_name_from_resume(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.hero.name == "Pawan Choudhary"


def test_parse_sets_hero_role_from_llm(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.hero.role  # non-empty


def test_parse_sets_hero_headline_from_llm(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.hero.headline


def test_parse_skills_are_skill_categories(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.skills
    assert all(isinstance(s, SkillCategory) for s in result.skills)


def test_parse_skills_categories_contain_known_skill(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    flat = [item for c in result.skills for item in c.items]
    assert "Python" in flat


def test_parse_projects_are_project_items(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert all(isinstance(p, ProjectItem) for p in result.projects)


def test_parse_project_has_title_technologies_and_outcome(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    first = result.projects[0]
    assert first.title == "AI Portfolio Generator"
    assert "Python" in first.technologies
    assert first.outcome


def test_parse_project_links_default_to_none(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.projects[0].github_url is None
    assert result.projects[0].demo_url is None


def test_parse_project_legacy_string_format_still_works(sample_resume, sample_analysis):
    """If a model ignores instructions and returns plain strings, parsing
    should still produce usable ProjectItems instead of failing."""
    data = json.loads(VALID_RESPONSE)
    data["projects"] = ["FastAPI Microservice: a containerised REST API."]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    assert isinstance(result.projects[0], ProjectItem)
    assert result.projects[0].title == "FastAPI Microservice"


def test_parse_career_paths_are_strings(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert all(isinstance(c, str) for c in result.career_paths)


def test_parse_contact_email_from_resume(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.contact.email == "pawan@example.com"


def test_parse_contact_linkedin_from_resume(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.contact.linkedin == "linkedin.com/in/pawan"


def test_parse_llm_model_stored(sample_resume, sample_analysis):
    result = _parse_portfolio_response(
        VALID_RESPONSE, sample_resume, sample_analysis, "qwen3:14b"
    )
    assert result.llm_model == "qwen3:14b"


def test_parse_strips_markdown_fence(sample_resume, sample_analysis):
    fenced = f"```json\n{VALID_RESPONSE}\n```"
    result = _parse_portfolio_response(
        fenced, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert isinstance(result, PortfolioSchema)


def test_parse_strips_prose_prefix(sample_resume, sample_analysis):
    with_prose = f"Here is the portfolio content:\n{VALID_RESPONSE}"
    result = _parse_portfolio_response(
        with_prose, sample_resume, sample_analysis, "qwen3:8b"
    )
    assert isinstance(result, PortfolioSchema)


def test_parse_empty_response_raises(sample_resume, sample_analysis):
    with pytest.raises(PortfolioGenerationError):
        _parse_portfolio_response("", sample_resume, sample_analysis, "qwen3:8b")


def test_parse_whitespace_only_raises(sample_resume, sample_analysis):
    with pytest.raises(PortfolioGenerationError):
        _parse_portfolio_response("   \n  ", sample_resume, sample_analysis, "qwen3:8b")


def test_parse_invalid_json_raises(sample_resume, sample_analysis):
    with pytest.raises(PortfolioGenerationError):
        _parse_portfolio_response(
            '{"hero_role": [unclosed', sample_resume, sample_analysis, "qwen3:8b"
        )


def test_parse_json_array_raises(sample_resume, sample_analysis):
    with pytest.raises(PortfolioGenerationError):
        _parse_portfolio_response(
            '["not", "an", "object"]', sample_resume, sample_analysis, "qwen3:8b"
        )


def test_parse_fallback_skills_from_resume(sample_resume, sample_analysis):
    """When skills key is missing from LLM response, fall back to resume.skills
    (still passed through categorization)."""
    data = json.loads(VALID_RESPONSE)
    del data["skills"]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    flat = sorted(item for c in result.skills for item in c.items)
    assert flat == sorted(sample_resume.skills)


def test_parse_fallback_career_paths_from_analysis(sample_resume, sample_analysis):
    """When career_paths is missing, fall back to analysis.recommended_career_paths."""
    data = json.loads(VALID_RESPONSE)
    del data["career_paths"]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.career_paths == sample_analysis.recommended_career_paths


def test_parse_fallback_projects_from_analysis(sample_resume, sample_analysis):
    """When projects is missing, fall back to analysis.recommended_projects,
    coerced into ProjectItem objects via the legacy-string heuristic."""
    data = json.loads(VALID_RESPONSE)
    del data["projects"]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    assert len(result.projects) == len(sample_analysis.recommended_projects)
    assert all(isinstance(p, ProjectItem) for p in result.projects)


def test_parse_fallback_about_from_analysis_summary(sample_resume, sample_analysis):
    """When about is missing, fall back to analysis.summary."""
    data = json.loads(VALID_RESPONSE)
    del data["about"]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.about == sample_analysis.summary


def test_parse_fallback_hero_role_from_analysis(sample_resume, sample_analysis):
    """When hero_role is missing, fall back to first recommended_career_path."""
    data = json.loads(VALID_RESPONSE)
    del data["hero_role"]
    result = _parse_portfolio_response(
        json.dumps(data), sample_resume, sample_analysis, "qwen3:8b"
    )
    assert result.hero.role == sample_analysis.recommended_career_paths[0]


# ── generate() ────────────────────────────────────────────────────────────────

def test_generate_returns_portfolio_schema(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = generate(sample_resume, sample_analysis)
    assert isinstance(result, PortfolioSchema)


def test_generate_populates_all_sections(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = generate(sample_resume, sample_analysis)
    assert result.hero.name
    assert result.hero.role
    assert result.hero.headline
    assert result.about
    assert result.skills
    assert result.projects
    assert result.career_paths


def test_generate_stores_model_name(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        result = generate(sample_resume, sample_analysis, model="qwen3:14b")
    assert result.llm_model == "qwen3:14b"


def test_generate_uses_default_model(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        generate(sample_resume, sample_analysis)
    assert "qwen3:8b" in str(MockClient.call_args)


def test_generate_passes_custom_host(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        generate(sample_resume, sample_analysis, host="http://myhost:11434")
    assert "myhost" in str(MockClient.call_args)


def test_generate_propagates_ollama_unavailable(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        mock = MagicMock()
        mock.generate.side_effect = OllamaUnavailableError("http://localhost:11434")
        MockClient.return_value = mock
        with pytest.raises(OllamaUnavailableError):
            generate(sample_resume, sample_analysis)


def test_generate_propagates_malformed_response(sample_resume, sample_analysis):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client("not json at all !!!")
        with pytest.raises(PortfolioGenerationError):
            generate(sample_resume, sample_analysis)


def test_generate_runs_validator(sample_resume, sample_analysis):
    """Validator is called — an otherwise-valid response that yields empty hero
    name should be caught by validate()."""
    # Use a resume with no personal info so name falls back to ""
    resume_no_name = ResumeSchema(
        filename="sample.pdf",
        raw_text="No name here",
        skills=["Python"],
    )
    data = json.loads(VALID_RESPONSE)
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(json.dumps(data))
        with pytest.raises(PortfolioValidationError):
            generate(resume_no_name, sample_analysis)


# ── generate_and_save() ───────────────────────────────────────────────────────

def test_generate_and_save_writes_file(sample_resume, sample_analysis, tmp_path):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(sample_resume, sample_analysis, output_dir=tmp_path)
    assert out.exists()
    assert out.suffix == ".json"


def test_generate_and_save_filename_uses_stem(sample_resume, sample_analysis, tmp_path):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(sample_resume, sample_analysis, output_dir=tmp_path)
    assert out.name == "sample_portfolio.json"


def test_generate_and_save_output_is_valid_json(sample_resume, sample_analysis, tmp_path):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(sample_resume, sample_analysis, output_dir=tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "hero" in data
    assert "about" in data
    assert "skills" in data
    assert "projects" in data
    assert "career_paths" in data
    assert "contact" in data
    assert "schema_version" in data


def test_generate_and_save_creates_nested_dir(sample_resume, sample_analysis, tmp_path):
    nested = tmp_path / "a" / "b"
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(sample_resume, sample_analysis, output_dir=nested)
    assert out.exists()


def test_generate_and_save_fallback_stem_when_no_filename(sample_analysis, tmp_path):
    resume = ResumeSchema(
        raw_text="text",
        skills=["Python"],
        personal=PersonalInfo(name="Pawan"),
    )
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(resume, sample_analysis, output_dir=tmp_path)
    assert out.name == "resume_portfolio.json"


def test_generate_and_save_json_contains_llm_model(sample_resume, sample_analysis, tmp_path):
    with patch("src.portfolio.portfolio_generator.OllamaClient") as MockClient:
        MockClient.return_value = _mock_client(VALID_RESPONSE)
        out = generate_and_save(
            sample_resume, sample_analysis, output_dir=tmp_path, model="qwen3:14b"
        )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["llm_model"] == "qwen3:14b"
