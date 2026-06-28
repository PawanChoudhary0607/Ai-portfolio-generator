"""Content density classification — the core of the Milestone 6 adaptive layer.

A single generator producing one fixed layout regardless of how much (or how
little) content arrives is the root cause behind most of the design-audit
findings: a 1-project, 1-skill, no-contact resume gets the exact same
section padding, hero treatment, and stat-bragging copy as a 5-project,
24-skill resume — so the sparser the input, the more obviously "templated"
the output looks.

This module classifies a WebsiteSchema as "sparse", "medium", or "dense"
based on how much real content it has. website_generator.py uses the result
to:
  - set a `data-density` attribute on <body> so each theme's CSS can scale
    its own spacing tokens (adaptive spacing)
  - decide whether to show volume-bragging UI like the modern-saas stats
    row (it makes sense at 5 projects, it's faintly absurd at 1)
"""

from __future__ import annotations

from typing import Literal

from src.website.website_schema import WebsiteSchema

Density = Literal["sparse", "medium", "dense"]

# Thresholds are intentionally simple and content-agnostic: this is a layout
# decision, not a judgement about the candidate. A "sparse" classification
# only ever affects spacing/visibility, never what content is shown.
_SPARSE_MAX_SCORE = 7
_DENSE_MIN_SCORE = 35


def _content_score(schema: WebsiteSchema) -> int:
    """A rough proxy for "how much is there to fill the page with".

    Projects are weighted heaviest since each one occupies far more
    vertical space than a single skill badge or career-path entry.
    """
    score = 0
    score += len(schema.projects.items) * 3
    score += len(schema.skills.categories)
    score += sum(len(c.items) for c in schema.skills.categories)
    score += len(schema.career_paths.items)
    return score


def classify_density(schema: WebsiteSchema) -> Density:
    """Classify a WebsiteSchema's overall content volume."""
    score = _content_score(schema)
    if score <= _SPARSE_MAX_SCORE:
        return "sparse"
    if score >= _DENSE_MIN_SCORE:
        return "dense"
    return "medium"
