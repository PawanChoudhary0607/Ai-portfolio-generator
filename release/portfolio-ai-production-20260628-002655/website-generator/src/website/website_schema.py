"""Pydantic v2 schema for website generation configuration.

This schema defines the contract between PortfolioSchema (Milestone 4)
and the website generator (Milestone 5). It carries all rendering
context — template choice, colour palette, and resolved section content —
so the template layer needs zero business logic.

Pipeline position:
    PortfolioSchema → WebsiteSchema → HTML / CSS / JSON output
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

WEBSITE_SCHEMA_VERSION = "6.0"


# ── Template Enum ─────────────────────────────────────────────────────────────

class TemplateTheme(str, Enum):
    """Available visual themes for the generated portfolio website.

    Each theme is a genuinely distinct layout — different page chrome,
    different section structures, different typography systems — not a
    palette swap of the same markup. See src/website/theme_renderers.py
    for the per-theme section builders.
    """

    MINIMAL = "minimal-white-orange"
    EXECUTIVE = "executive-black-gold"
    DEVELOPER = "developer-dark"
    CREATIVE = "creative-portfolio"
    SAAS = "modern-saas"


# ── Section models ────────────────────────────────────────────────────────────

class HeroContent(BaseModel):
    """Content resolved for the hero / banner section."""

    name: str = Field(default="")
    role: str = Field(default="")
    headline: str = Field(default="")
    initials: str = Field(default="")          # derived: first + last initial


class AboutContent(BaseModel):
    """Content for the about / bio section."""

    bio: str = Field(default="")


class SkillCategoryContent(BaseModel):
    """A named group of skills, resolved for rendering."""

    category: str = Field(default="")
    items: list[str] = Field(default_factory=list)


class SkillsContent(BaseModel):
    """Content for the skills section."""

    categories: list[SkillCategoryContent] = Field(default_factory=list)


class ProjectContent(BaseModel):
    """A single, structured project entry in the projects section."""

    title: str = Field(default="")
    problem: str = Field(default="")
    technologies: list[str] = Field(default_factory=list)
    outcome: str = Field(default="")
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    index: int = Field(default=0)              # 1-based display order
    is_featured: bool = Field(default=False)   # first project gets spotlight treatment


class ProjectsContent(BaseModel):
    """Content for the projects section (collection)."""

    items: list[ProjectContent] = Field(default_factory=list)


class CareerPathContent(BaseModel):
    """A single career path entry."""

    title: str = Field(default="")
    icon: str = Field(default="🚀")            # emoji icon for visual variety
    index: int = Field(default=0)


class CareerPathsContent(BaseModel):
    """Content for the career paths section."""

    items: list[CareerPathContent] = Field(default_factory=list)


class ContactContent(BaseModel):
    """Content for the contact section."""

    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    has_contact_info: bool = Field(default=False)


# ── Root schema ───────────────────────────────────────────────────────────────

class WebsiteSchema(BaseModel):
    """All data needed to render a portfolio website.

    Constructed by website_generator.build_website_schema() from a
    PortfolioSchema.  Never holds raw AI output directly.
    """

    schema_version: str = Field(default=WEBSITE_SCHEMA_VERSION)
    theme: TemplateTheme = Field(default=TemplateTheme.MINIMAL)

    # ── Resolved section content ──────────────────────────────────────────────
    hero: HeroContent
    about: AboutContent
    skills: SkillsContent
    projects: ProjectsContent
    career_paths: CareerPathsContent
    contact: ContactContent

    # ── Meta ─────────────────────────────────────────────────────────────────
    page_title: str = Field(default="")        # <title> tag value
    llm_model: str = Field(default="")         # forwarded from PortfolioSchema
