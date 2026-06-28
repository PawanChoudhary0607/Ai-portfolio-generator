"""Portfolio content generation pipeline.

Pipeline:
    ResumeSchema + AIAnalysisSchema → Prompt Builder → Ollama Client → PortfolioSchema

This module owns the generation pipeline. It never parses JSON directly and
never calls Ollama directly — those concerns belong to _parse_portfolio_response()
and OllamaClient respectively.

Design invariants:
- Raises only typed exceptions from src.portfolio.exceptions or src.ai.exceptions.
- No bare dicts are passed across module boundaries.
- The OllamaClient is the sole network I/O point.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.exceptions import AIError
from src.ai.ollama_client import OllamaClient
from src.portfolio.exceptions import PortfolioGenerationError
from src.portfolio.portfolio_schema import (
    ContactInfo,
    HeroSection,
    PortfolioSchema,
    ProjectItem,
    SkillCategory,
)
from src.portfolio.portfolio_validator import validate
from src.schemas.resume import ResumeSchema

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen3:8b"
DEFAULT_OUTPUT_DIR = "data/processed"

# Strip optional markdown code fences the model may emit
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

_SYSTEM_INSTRUCTIONS = """\
You are a professional portfolio content writer and senior technical recruiter.
Given a resume and an AI career analysis, generate structured portfolio content
that reads like it was written by the candidate themselves, not a generic AI
summary. Be specific and concrete — prefer real nouns and numbers from the
resume over vague phrases like "various technologies" or "leveraged synergies".
Return a JSON object only — no markdown, no code fences, no prose outside the JSON.

The JSON object must have exactly these keys:

- hero_role: string. The candidate's primary professional role/title
  (e.g. "Python & ML Engineer"), max 60 chars.

- hero_headline: string. A single, concrete sentence describing what the
  candidate builds and for whom — written like a real portfolio homepage,
  not a resume objective. Max 120 chars.
  Good example: "Building AI products and developer tools that turn messy
  data into something people actually want to use."
  Bad example: "Highly motivated professional seeking opportunities to
  leverage skills."

- about: string. A 3–4 sentence professional bio in third person that reads
  as a narrative — what the candidate works on, what they care about, and
  what kind of role they're suited for next. It must NOT restate the resume
  as a list of facts or repeat skills/employers verbatim; synthesize instead.

- skills: list of strings. Flat list of the candidate's strongest concrete
  skills, tools, and technologies (not soft skills). Drawn from the resume.

- projects: list of JSON objects, each with exactly these keys:
    - title: short, specific project name (max 60 chars, no trailing period)
    - problem: one sentence on the real-world problem the project solves
    - technologies: list of strings — the specific tools/languages/frameworks used
    - outcome: one sentence on the measurable or demonstrable result
  Provide 2–4 projects. Base these on the candidate's actual resume/analysis
  content — do not invent unrelated technologies.

- career_paths: list of strings (realistic career paths, copied from the analysis)

Every key must be present. Lists must contain at least one item.
Return only the JSON object. Nothing else.\
"""

# ── Deterministic skill categorization ──────────────────────────────────────
#
# Categorization is done in code rather than left to the LLM. The LLM's flat
# "skills" list is free-form text and its grouping behavior is not reliable
# across models — a keyword classifier here guarantees consistent category
# names and ordering every time, regardless of which model produced the list.

_SKILL_CATEGORY_ORDER = [
    "Programming Languages",
    "AI / ML",
    "Frameworks",
    "Cloud",
    "Tools",
]

_SKILL_CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "Programming Languages": {
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "sql", "html", "css", "bash", "shell", "matlab", "dart",
        "perl", "objective-c", "elixir", "haskell",
    },
    "AI / ML": {
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "llm", "llms", "ollama", "langchain", "transformers",
        "huggingface", "hugging face", "opencv", "pandas", "numpy",
        "ai", "ml", "generative ai", "rag", "prompt engineering",
        "neural networks", "data science", "xgboost",
    },
    "Frameworks": {
        "fastapi", "django", "flask", "react", "next.js", "nextjs",
        "vue", "angular", "node.js", "nodejs", "express", "spring",
        "spring boot", ".net", "rails", "laravel", "streamlit",
        "svelte", "nestjs", "graphql",
    },
    "Cloud": {
        "aws", "gcp", "azure", "google cloud", "amazon web services",
        "kubernetes", "k8s", "terraform", "lambda", "ec2", "s3",
        "cloudformation", "heroku", "vercel", "digitalocean",
        "firebase", "supabase",
    },
    "Tools": {
        "git", "docker", "github", "gitlab", "ci/cd", "jenkins",
        "linux", "postgresql", "postgres", "mysql", "mongodb", "redis",
        "jira", "figma", "postman", "nginx", "rest api", "graphql api",
        "elasticsearch", "kafka", "rabbitmq", "grafana", "prometheus",
    },
}


def _categorize_skills(skills: list[str]) -> list[SkillCategory]:
    """Group a flat skill list into named categories.

    Unrecognized skills fall into an "Other" category appended at the end
    rather than being dropped, so no candidate skill is ever lost.
    """
    buckets: dict[str, list[str]] = {name: [] for name in _SKILL_CATEGORY_ORDER}
    other: list[str] = []

    for skill in skills:
        skill_clean = skill.strip()
        if not skill_clean:
            continue
        key = skill_clean.lower()
        placed = False
        for category in _SKILL_CATEGORY_ORDER:
            if key in _SKILL_CATEGORY_KEYWORDS[category]:
                buckets[category].append(skill_clean)
                placed = True
                break
        if not placed:
            other.append(skill_clean)

    categories = [
        SkillCategory(category=name, items=items)
        for name, items in buckets.items()
        if items
    ]
    if other:
        categories.append(SkillCategory(category="Other", items=other))

    return categories


def _build_portfolio_prompt(
    resume: ResumeSchema,
    analysis: AIAnalysisSchema,
) -> str:
    """Compose the LLM prompt from resume and analysis data."""
    lines: list[str] = []

    # Resume context
    if resume.personal:
        if resume.personal.name:
            lines.append(f"Candidate name: {resume.personal.name}")
        if resume.personal.location:
            lines.append(f"Location: {resume.personal.location}")

    if resume.skills:
        lines.append(f"Skills: {', '.join(resume.skills)}")

    if resume.summary:
        lines.append(f"Resume summary: {resume.summary}")

    if resume.experience_raw:
        lines.append(f"Experience:\n{resume.experience_raw[:800]}")

    if resume.projects_raw:
        lines.append(f"Projects:\n{resume.projects_raw[:600]}")

    # Analysis context
    lines.append(f"\nAI Analysis summary: {analysis.summary}")
    lines.append(f"Strengths: {', '.join(analysis.strengths)}")
    lines.append(f"Recommended projects: {'; '.join(analysis.recommended_projects)}")
    lines.append(f"Career paths: {', '.join(analysis.recommended_career_paths)}")

    resume_block = "\n".join(lines)

    return f"""{_SYSTEM_INSTRUCTIONS}

---CANDIDATE DATA---
{resume_block}
---END DATA---

Return the JSON object now:"""


def _extract_json(text: str) -> str:
    """Extract the JSON object from raw model output."""
    text = text.strip()

    fence_match = _FENCE_RE.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _split_title_and_description(raw: str, idx: int) -> tuple[str, str]:
    """Fallback heuristic for legacy plain-string project descriptions.

    Only used if the model ignores instructions and returns a string
    instead of a project object — keeps generation resilient rather than
    failing outright.
    """
    raw = raw.strip()
    if not raw:
        return f"Project {idx + 1}", ""

    for sep in [":", " - ", "\n"]:
        if sep in raw:
            title, _, rest = raw.partition(sep)
            title = title.strip()
            rest = rest.strip()
            if title and len(title) <= 80 and rest:
                return title, rest

    if len(raw) <= 60:
        return raw, ""
    return raw[:57].rstrip() + "…", raw


def _coerce_project(raw: object, idx: int) -> ProjectItem:
    """Build a ProjectItem from either a structured dict or a legacy string."""
    if isinstance(raw, dict):
        title = str(raw.get("title", "")).strip() or f"Project {idx + 1}"
        problem = str(raw.get("problem", "")).strip()
        technologies = [
            str(t).strip() for t in raw.get("technologies", []) if str(t).strip()
        ] if isinstance(raw.get("technologies"), list) else []
        outcome = str(raw.get("outcome", "")).strip()
        if not problem and not outcome:
            # Model returned an object with no usable prose — nothing to recover.
            problem = problem or "Details to be added."
            outcome = outcome or "Details to be added."
        return ProjectItem(
            title=title,
            problem=problem or "Details to be added.",
            technologies=technologies,
            outcome=outcome or "Details to be added.",
        )

    # Legacy plain-string format
    title, rest = _split_title_and_description(str(raw), idx)
    return ProjectItem(
        title=title,
        problem=rest or "Details to be added.",
        technologies=[],
        outcome="Details to be added.",
    )


def _parse_portfolio_response(
    raw_response: str,
    resume: ResumeSchema,
    analysis: AIAnalysisSchema,
    model: str,
) -> PortfolioSchema:
    """Parse and assemble a PortfolioSchema from the raw LLM response.

    Falls back to safe defaults for every field that is missing or invalid
    so a result is always returned when the raw_response is parseable JSON.

    Raises:
        PortfolioGenerationError: response is not parseable JSON.
    """
    if not raw_response or not raw_response.strip():
        raise PortfolioGenerationError("empty response from model")

    json_str = _extract_json(raw_response)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise PortfolioGenerationError(f"JSON decode error: {e}") from e

    if not isinstance(data, dict):
        raise PortfolioGenerationError(
            f"expected JSON object, got {type(data).__name__}"
        )

    # ── Hero section ──────────────────────────────────────────────────────────
    name = ""
    if resume.personal and resume.personal.name:
        name = resume.personal.name

    hero = HeroSection(
        name=name,
        role=str(data.get("hero_role", "")).strip()
        or (analysis.recommended_career_paths[0] if analysis.recommended_career_paths else ""),
        headline=str(data.get("hero_headline", "")).strip()
        or analysis.summary[:120],
    )

    # ── About ─────────────────────────────────────────────────────────────────
    about = str(data.get("about", "")).strip() or analysis.summary

    # ── Skills ───────────────────────────────────────────────────────────────
    raw_skills = data.get("skills", [])
    flat_skills: list[str] = (
        [str(s).strip() for s in raw_skills if str(s).strip()]
        if isinstance(raw_skills, list)
        else resume.skills
    ) or resume.skills
    skills = _categorize_skills(flat_skills)

    # ── Projects ─────────────────────────────────────────────────────────────
    raw_projects = data.get("projects", [])
    if not isinstance(raw_projects, list) or not raw_projects:
        raw_projects = list(analysis.recommended_projects)
    projects = [_coerce_project(p, idx) for idx, p in enumerate(raw_projects)]

    # ── Career paths ──────────────────────────────────────────────────────────
    raw_paths = data.get("career_paths", [])
    career_paths: list[str] = (
        [str(c).strip() for c in raw_paths if str(c).strip()]
        if isinstance(raw_paths, list)
        else analysis.recommended_career_paths
    ) or analysis.recommended_career_paths

    # ── Contact ───────────────────────────────────────────────────────────────
    contact = ContactInfo(
        email=resume.personal.email if resume.personal else None,
        phone=resume.personal.phone if resume.personal else None,
        location=resume.personal.location if resume.personal else None,
        linkedin=resume.personal.linkedin if resume.personal else None,
    )

    return PortfolioSchema(
        llm_model=model,
        hero=hero,
        about=about,
        skills=skills,
        projects=projects,
        career_paths=career_paths,
        contact=contact,
    )


def generate(
    resume: ResumeSchema,
    analysis: AIAnalysisSchema,
    model: str = DEFAULT_MODEL,
    host: str = "http://localhost:11434",
    timeout: int = 120,
) -> PortfolioSchema:
    """Generate a validated PortfolioSchema from resume and analysis.

    Args:
        resume:   Validated ResumeSchema from Milestone 2 pipeline.
        analysis: Validated AIAnalysisSchema from Milestone 3 pipeline.
        model:    Ollama model name.
        host:     Ollama server URL.
        timeout:  Request timeout in seconds.

    Returns:
        Validated PortfolioSchema.

    Raises:
        PortfolioGenerationError: LLM response is unusable.
        PortfolioValidationError: Assembled schema fails validation.
        OllamaUnavailableError, ModelNotFoundError, OllamaTimeoutError,
        MalformedResponseError — all from src.ai.exceptions.
    """
    client = OllamaClient(model=model, host=host, timeout=timeout)
    prompt = _build_portfolio_prompt(resume, analysis)

    name = resume.personal.name if resume.personal else "unknown"
    logger.info("Generating portfolio for: %s", name)

    raw_response = client.generate(prompt)
    portfolio = _parse_portfolio_response(raw_response, resume, analysis, model)
    validate(portfolio)

    logger.info(
        "Portfolio generated — %d skill categories, %d projects, %d career paths",
        len(portfolio.skills),
        len(portfolio.projects),
        len(portfolio.career_paths),
    )

    return portfolio


def generate_and_save(
    resume: ResumeSchema,
    analysis: AIAnalysisSchema,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    model: str = DEFAULT_MODEL,
    host: str = "http://localhost:11434",
    timeout: int = 120,
) -> Path:
    """Generate a portfolio and save PortfolioSchema as JSON.

    Returns the path of the written JSON file.
    """
    portfolio = generate(resume, analysis, model=model, host=host, timeout=timeout)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(resume.filename).stem if resume.filename else "resume"
    output_path = output_dir / f"{stem}_portfolio.json"

    output_path.write_text(
        json.dumps(
            portfolio.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    logger.info("Saved portfolio to: %s", output_path)
    return output_path
