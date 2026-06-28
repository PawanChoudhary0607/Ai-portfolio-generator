"""Validate a fully constructed PortfolioSchema before it is written to disk.

Rules enforced here go beyond Pydantic's type checks — they test business
invariants: non-empty strings, non-empty lists, reasonable lengths, etc.

This module raises only PortfolioValidationError — never returns partial data.
"""

from __future__ import annotations

from src.portfolio.exceptions import PortfolioValidationError

# Forward reference resolved at call-time to avoid circular imports
# (portfolio_schema imports nothing from this module)


def validate(portfolio: "PortfolioSchema") -> None:  # noqa: F821
    """Validate a PortfolioSchema instance.

    Raises:
        PortfolioValidationError: on the first invalid field found.
    """
    # ── Hero ─────────────────────────────────────────────────────────────────
    if not portfolio.hero.name.strip():
        raise PortfolioValidationError("hero.name", "must be a non-empty string")

    if not portfolio.hero.role.strip():
        raise PortfolioValidationError("hero.role", "must be a non-empty string")

    if not portfolio.hero.headline.strip():
        raise PortfolioValidationError("hero.headline", "must be a non-empty string")

    # ── About ─────────────────────────────────────────────────────────────────
    if not portfolio.about.strip():
        raise PortfolioValidationError("about", "must be a non-empty string")

    # ── Skills (grouped by category) ─────────────────────────────────────────
    if not portfolio.skills:
        raise PortfolioValidationError(
            "skills", "must contain at least one skill category"
        )

    for i, category in enumerate(portfolio.skills):
        if not category.category.strip():
            raise PortfolioValidationError(
                f"skills[{i}].category", "must be a non-empty string"
            )
        if not category.items:
            raise PortfolioValidationError(
                f"skills[{i}].items", "must contain at least one skill"
            )
        for j, item in enumerate(category.items):
            if not isinstance(item, str) or not item.strip():
                raise PortfolioValidationError(
                    f"skills[{i}].items[{j}]", "each skill must be a non-empty string"
                )

    # ── Projects (structured) ────────────────────────────────────────────────
    if not portfolio.projects:
        raise PortfolioValidationError(
            "projects", "must contain at least one project"
        )

    for i, project in enumerate(portfolio.projects):
        if not project.title.strip():
            raise PortfolioValidationError(
                f"projects[{i}].title", "must be a non-empty string"
            )
        if not project.problem.strip():
            raise PortfolioValidationError(
                f"projects[{i}].problem", "must be a non-empty string"
            )
        if not project.outcome.strip():
            raise PortfolioValidationError(
                f"projects[{i}].outcome", "must be a non-empty string"
            )
        for j, tech in enumerate(project.technologies):
            if not isinstance(tech, str) or not tech.strip():
                raise PortfolioValidationError(
                    f"projects[{i}].technologies[{j}]",
                    "each technology must be a non-empty string",
                )

    # ── Career paths ──────────────────────────────────────────────────────────
    if not portfolio.career_paths:
        raise PortfolioValidationError(
            "career_paths", "must contain at least one career path"
        )

    for i, path in enumerate(portfolio.career_paths):
        if not isinstance(path, str) or not path.strip():
            raise PortfolioValidationError(
                f"career_paths[{i}]", "each career path must be a non-empty string"
            )

    # ── Schema metadata ───────────────────────────────────────────────────────
    if not portfolio.schema_version.strip():
        raise PortfolioValidationError(
            "schema_version", "must be a non-empty string"
        )
