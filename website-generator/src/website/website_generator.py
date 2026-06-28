"""Website generation pipeline for Milestone 5.

Pipeline position:
    PortfolioSchema → WebsiteSchema → index.html + styles.css + portfolio_data.json

Design invariants:
- Raises only typed exceptions from src.website.exceptions.
- No bare dicts are passed across module boundaries.
- Templates are resolved at import time so missing files fail fast.
- The output directory is always returned as a resolved Path.
- All layout decisions live in theme_renderers.py — this module only owns
  data shaping (build_website_schema) and template I/O (render/generate).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from src.portfolio.portfolio_schema import PortfolioSchema
from src.website import theme_renderers
from src.website.content_density import classify_density
from src.website.exceptions import WebsiteGenerationError
from src.website.render_utils import build_initials, escape, headline_size_class, name_size_class
from src.website.website_schema import (
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

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent / "templates"
DEFAULT_OUTPUT_BASE = Path("data/output")

# Emoji icons cycled for career path cards (used by themes that want them)
_CAREER_ICONS = ["🚀", "💡", "🔧", "📊", "🎯", "🌐", "⚡", "🛠️", "📈", "🤖"]

# ── Schema builder ─────────────────────────────────────────────────────────────


def build_website_schema(
    portfolio: PortfolioSchema,
    theme: TemplateTheme = TemplateTheme.MINIMAL,
) -> WebsiteSchema:
    """Transform a PortfolioSchema into a WebsiteSchema.

    All business logic for rendering *decisions* (not layout — that's
    theme_renderers.py) lives here so the template layer stays as dumb
    string substitution.
    """
    name = portfolio.hero.name or ""
    initials = build_initials(name)

    hero = HeroContent(
        name=name,
        role=portfolio.hero.role or "",
        headline=portfolio.hero.headline or "",
        initials=initials,
    )

    about = AboutContent(bio=portfolio.about or "")

    skills = SkillsContent(
        categories=[
            SkillCategoryContent(category=c.category, items=list(c.items))
            for c in portfolio.skills
        ]
    )

    project_items = [
        ProjectContent(
            title=p.title,
            problem=p.problem,
            technologies=list(p.technologies),
            outcome=p.outcome,
            github_url=p.github_url,
            demo_url=p.demo_url,
            index=idx + 1,
            is_featured=(idx == 0),
        )
        for idx, p in enumerate(portfolio.projects)
    ]
    projects = ProjectsContent(items=project_items)

    career_items = [
        CareerPathContent(
            title=path,
            icon=_CAREER_ICONS[idx % len(_CAREER_ICONS)],
            index=idx + 1,
        )
        for idx, path in enumerate(portfolio.career_paths)
    ]
    career_paths = CareerPathsContent(items=career_items)

    c = portfolio.contact
    has_any = any([c.email, c.phone, c.location, c.linkedin])
    contact = ContactContent(
        email=c.email,
        phone=c.phone,
        location=c.location,
        linkedin=c.linkedin,
        has_contact_info=has_any,
    )

    page_title = f"{name} — Portfolio" if name else "Portfolio"

    return WebsiteSchema(
        theme=theme,
        hero=hero,
        about=about,
        skills=skills,
        projects=projects,
        career_paths=career_paths,
        contact=contact,
        page_title=page_title,
        llm_model=portfolio.llm_model,
    )


# ── Template rendering ─────────────────────────────────────────────────────────


# Conditional blocks are wrapped in HTML comment markers in each theme's
# index.html: <!--@if:KEY--> ... <!--@endif:KEY-->. _strip_conditional()
# removes a marked block entirely when its condition is false — this is how
# "empty section removal" works (e.g. no contact info → the whole Contact
# section, its nav link, and the saas CTA button disappear, rather than
# rendering a "No contact information provided." fallback message).
_CONDITIONAL_RE_CACHE: dict[str, re.Pattern] = {}


def _conditional_pattern(key: str) -> re.Pattern:
    if key not in _CONDITIONAL_RE_CACHE:
        _CONDITIONAL_RE_CACHE[key] = re.compile(
            rf"<!--@if:{key}-->.*?<!--@endif:{key}-->", re.DOTALL
        )
    return _CONDITIONAL_RE_CACHE[key]


def _strip_conditional(html: str, key: str, keep: bool) -> str:
    """Remove (or unwrap) a `<!--@if:key--> ... <!--@endif:key-->` block.

    If keep is True, the markers are stripped but the content is kept.
    If keep is False, the entire block — markers and content — is removed.
    """
    pattern = _conditional_pattern(key)
    if keep:
        return pattern.sub(lambda m: m.group(0).replace(f"<!--@if:{key}-->", "").replace(f"<!--@endif:{key}-->", ""), html)
    return pattern.sub("", html)


def _get_template_dir(theme: TemplateTheme) -> Path:
    """Resolve and validate the template directory for *theme*."""
    tdir = TEMPLATES_DIR / theme.value
    if not tdir.is_dir():
        raise WebsiteGenerationError(f"template directory not found: {tdir}")
    return tdir


def _read_template(path: Path) -> str:
    """Read a template file, raising WebsiteGenerationError on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WebsiteGenerationError(f"cannot read template {path}: {exc}") from exc


def render(schema: WebsiteSchema) -> dict[str, str]:
    """Render a WebsiteSchema into a dict of filename → content strings.

    Returns:
        {"index.html": "...", "styles.css": "...", "portfolio_data.json": "..."}

    Raises:
        WebsiteGenerationError: A template file is missing or unreadable.
    """
    tdir = _get_template_dir(schema.theme)

    html_template = _read_template(tdir / "index.html")
    css_content = _read_template(tdir / "styles.css")

    density = classify_density(schema)

    # The modern-saas stats row exists to brag about volume ("5 Projects,
    # 5 Skill Areas..."); for a sparse profile it just broadcasts "1, 1, 1"
    # in the candidate's least favorable light, so it's omitted entirely
    # rather than rendered with deflating numbers.
    stats_row = (
        ""
        if density == "sparse"
        else theme_renderers.render_saas_stats_row(
            skill_count=len(schema.skills.categories),
            project_count=len(schema.projects.items),
            path_count=len(schema.career_paths.items),
        )
    )

    replacements = {
        "{{page_title}}":    escape(schema.page_title),
        "{{hero_name}}":     escape(schema.hero.name),
        "{{hero_role}}":     escape(schema.hero.role),
        "{{hero_headline}}": escape(schema.hero.headline),
        "{{hero_initials}}": escape(schema.hero.initials),
        "{{hero_extra}}":    theme_renderers.render_hero_extra(schema.theme, schema.hero, schema.contact),
        "{{hero_social}}":   theme_renderers.render_social(schema.theme, schema.contact),
        "{{about_bio}}":     escape(schema.about.bio),
        "{{skills_markup}}":  theme_renderers.render_skills(schema.theme, schema.skills.categories),
        "{{project_markup}}": theme_renderers.render_projects(schema.theme, schema.projects.items),
        "{{career_markup}}":  theme_renderers.render_career(schema.theme, schema.career_paths.items),
        "{{contact_markup}}": theme_renderers.render_contact(schema.theme, schema.contact),
        "{{stats_row}}":     stats_row,
        # Adaptive layout hooks (Milestone 6) ───────────────────────────────
        "{{density}}":            density,
        "{{name_size_class}}":    name_size_class(schema.hero.name),
        "{{headline_size_class}}": headline_size_class(schema.hero.headline),
    }

    html = html_template

    # Empty section removal: strip the whole Contact section (and any nav
    # link / CTA button pointing at it) when there's genuinely nothing to
    # show, instead of rendering a "No contact information provided."
    # fallback inside an otherwise fully-styled section.
    html = _strip_conditional(html, "contact", keep=schema.contact.has_contact_info)

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    portfolio_data = {
        "schema_version": schema.schema_version,
        "theme": schema.theme.value,
        "density": density,
        "hero": schema.hero.model_dump(),
        "about": schema.about.bio,
        "skills": [c.model_dump() for c in schema.skills.categories],
        "projects": [p.model_dump() for p in schema.projects.items],
        "career_paths": [c.model_dump() for c in schema.career_paths.items],
        "contact": schema.contact.model_dump(),
        "page_title": schema.page_title,
        "llm_model": schema.llm_model,
    }

    return {
        "index.html": html,
        "styles.css": css_content,
        "portfolio_data.json": json.dumps(portfolio_data, ensure_ascii=False, indent=2),
    }


# ── Public high-level API ──────────────────────────────────────────────────────


def generate(
    portfolio: PortfolioSchema,
    output_dir: str | Path,
    theme: TemplateTheme = TemplateTheme.MINIMAL,
) -> Path:
    """Generate a static portfolio website from a PortfolioSchema.

    Returns:
        Resolved Path to the output directory.

    Raises:
        WebsiteGenerationError: Template missing or output write fails.
    """
    schema = build_website_schema(portfolio, theme=theme)
    files = render(schema)

    output_dir = Path(output_dir).resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WebsiteGenerationError(f"cannot create output directory {output_dir}: {exc}") from exc

    for filename, content in files.items():
        dest = output_dir / filename
        try:
            dest.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise WebsiteGenerationError(f"cannot write {dest}: {exc}") from exc

    logger.info(
        "Website generated — theme=%s files=%s output=%s",
        theme.value, list(files.keys()), output_dir,
    )
    return output_dir


def generate_from_json(
    portfolio_json_path: str | Path,
    output_dir: str | Path | None = None,
    theme: TemplateTheme = TemplateTheme.MINIMAL,
) -> Path:
    """Load a PortfolioSchema JSON file and generate a website.

    Convenience wrapper used by the CLI ``website`` command.

    Raises:
        WebsiteGenerationError: JSON load or generation failed.
    """
    portfolio_json_path = Path(portfolio_json_path)

    try:
        raw = portfolio_json_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        portfolio = PortfolioSchema.model_validate(data)
    except (OSError, json.JSONDecodeError, Exception) as exc:
        raise WebsiteGenerationError(
            f"cannot load portfolio JSON from {portfolio_json_path}: {exc}"
        ) from exc

    if output_dir is None:
        stem = portfolio_json_path.stem
        folder = re.sub(r"_portfolio$", "", stem) + "_portfolio_site"
        output_dir = DEFAULT_OUTPUT_BASE / folder

    return generate(portfolio, output_dir=output_dir, theme=theme)
