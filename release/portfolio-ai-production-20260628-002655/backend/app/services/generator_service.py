"""The isolation boundary between this SaaS backend and the frozen
`website-generator/` engine.

Rule for this whole codebase: **no other module imports anything from
`website-generator/src`.** Routes and other services call the plain
functions defined here, which take/return either primitives or this
backend's own Pydantic schemas — never the engine's internal types
directly past this module. That means the engine can be upgraded,
swapped, or even moved behind a separate microservice later without
touching a single route.

The engine itself is not modified — it's imported as a library by
adding `website-generator/` to `sys.path`.
"""

from __future__ import annotations

import logging
import sys
import json
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

if str(settings.GENERATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(settings.GENERATOR_ROOT))

# These imports reach into the frozen engine. Everything past this point
# in the file is the only place in the backend allowed to do that.
from src.ai import analyzer  # noqa: E402
from src.ai import exceptions as ai_exceptions  # noqa: E402
from src.extraction import exceptions as extraction_exceptions  # noqa: E402
from src.extraction import pdf_extractor  # noqa: E402
from src.parsing import resume_parser  # noqa: E402
from src.portfolio import exceptions as portfolio_exceptions  # noqa: E402
from src.portfolio import portfolio_generator  # noqa: E402
from src.website import exceptions as website_exceptions  # noqa: E402
from src.website.website_generator import build_website_schema, render  # noqa: E402
from src.website.website_schema import TemplateTheme  # noqa: E402


class GeneratorServiceError(Exception):
    """Backend-facing error wrapping any failure from the engine.

    Routes only ever need to catch this one type — `original` carries the
    engine-specific exception for logging, and `stage` says which pipeline
    step failed so the Step-2 processing UI can highlight the right row.

    `message` is always written to be safely shown to an end user: it never
    contains filesystem paths, hosts, model names, or other internal detail.
    The original exception (with full technical detail) is logged here and
    kept on `.original` for server-side debugging only — callers must never
    forward `original` to an API response.
    """

    def __init__(self, stage: str, message: str, original: Exception | None = None) -> None:
        self.stage = stage
        self.original = original
        if original is not None:
            logger.warning("Generator stage '%s' failed: %s", stage, original, exc_info=original)
        super().__init__(message)


_FRIENDLY_MESSAGES: dict[type[Exception], str] = {
    extraction_exceptions.PDFNotFoundError: (
        "We couldn't find the file you uploaded. Please try uploading it again."
    ),
    extraction_exceptions.InvalidPDFError: (
        "This file doesn't look like a valid PDF. Please upload a non-corrupted PDF resume."
    ),
    extraction_exceptions.EmptyPDFError: (
        "We couldn't find any readable text in this PDF — it may be a scanned or "
        "image-only document. Scanned PDFs aren't supported yet; try exporting your "
        "resume as a text-based PDF and uploading again."
    ),
    extraction_exceptions.SchemaValidationError: (
        "We had trouble reading the structure of this resume. Please try a different PDF export."
    ),
    extraction_exceptions.OutputWriteError: (
        "Something went wrong saving your file on our end. Please try again in a moment."
    ),
    ai_exceptions.OllamaUnavailableError: (
        "Our AI engine is temporarily unavailable. Please try again shortly."
    ),
    ai_exceptions.ModelNotFoundError: (
        "Our AI engine isn't configured correctly right now. Please try again later."
    ),
    ai_exceptions.OllamaTimeoutError: (
        "Analyzing your resume is taking longer than expected. Please try again."
    ),
    ai_exceptions.MalformedResponseError: (
        "We had trouble analyzing your resume. Please try again."
    ),
    ai_exceptions.SchemaValidationError: (
        "We had trouble analyzing your resume. Please try again."
    ),
    portfolio_exceptions.PortfolioGenerationError: (
        "We had trouble generating your portfolio content. Please try again."
    ),
    portfolio_exceptions.PortfolioValidationError: (
        "We had trouble generating your portfolio content. Please try again."
    ),
    website_exceptions.WebsiteGenerationError: (
        "We had trouble preparing your website. Please try again."
    ),
}

_GENERIC_FRIENDLY_MESSAGE = "Something went wrong while processing your resume. Please try again."


def _friendly_message(exc: Exception) -> str:
    """Maps a known engine exception to client-safe copy. Anything not in
    the table above falls back to a generic message rather than risk
    leaking technical detail for an exception type we didn't anticipate.
    """
    return _FRIENDLY_MESSAGES.get(type(exc), _GENERIC_FRIENDLY_MESSAGE)


# ── Theme catalog ────────────────────────────────────────────────────────
# Exposed to the frontend via /api/v1/themes. Labels/descriptions are
# presentation metadata owned by the backend, not the engine.

THEME_CATALOG: list[dict[str, str]] = [
    {
        "value": TemplateTheme.MINIMAL.value,
        "label": "Minimal",
        "description": "Clean white layout with orange accents and generous whitespace.",
    },
    {
        "value": TemplateTheme.EXECUTIVE.value,
        "label": "Executive",
        "description": "Black-and-gold layout for senior, leadership-oriented profiles.",
    },
    {
        "value": TemplateTheme.DEVELOPER.value,
        "label": "Developer",
        "description": "Dark, monospace-forward layout suited to engineering portfolios.",
    },
    {
        "value": TemplateTheme.CREATIVE.value,
        "label": "Creative",
        "description": "Expressive layout with bolder type and imagery for creative work.",
    },
    {
        "value": TemplateTheme.SAAS.value,
        "label": "Modern SaaS",
        "description": "Product-style layout modeled on modern SaaS marketing sites.",
    },
]

VALID_THEME_VALUES: set[str] = {t["value"] for t in THEME_CATALOG}


# ── Pipeline steps ───────────────────────────────────────────────────────


def extract_resume_text(pdf_path: Path) -> tuple[int, str]:
    """Stage 1: pull raw text out of the uploaded PDF."""
    try:
        return pdf_extractor.read_pdf(pdf_path)
    except extraction_exceptions.ExtractionError as exc:
        raise GeneratorServiceError("extraction", _friendly_message(exc), original=exc) from exc


def parse_resume(raw_text: str, *, filename: str, page_count: int) -> dict[str, Any]:
    """Stage 1b: turn raw text into a structured ResumeSchema dict."""
    try:
        resume_schema = resume_parser.parse(raw_text, filename=filename, page_count=page_count)
    except Exception as exc:  # parser is best-effort and rarely raises, but stay safe
        raise GeneratorServiceError(
            "extraction",
            "We had trouble reading the structure of this resume. Please try a different PDF export.",
            original=exc,
        ) from exc
    return resume_schema.model_dump(mode="json")


def analyze_resume(resume_schema_dict: dict[str, Any]) -> dict[str, Any]:
    """Stage 2: run the local-LLM analysis pass over the parsed resume."""
    from src.schemas.resume import ResumeSchema

    resume_schema = ResumeSchema.model_validate(resume_schema_dict)
    try:
        analysis = analyzer.analyze(
            resume_schema,
            model=settings.OLLAMA_MODEL,
            host=settings.OLLAMA_HOST,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
    except ai_exceptions.AIError as exc:
        raise GeneratorServiceError("ai_analysis", _friendly_message(exc), original=exc) from exc
    return analysis.model_dump(mode="json")


def generate_portfolio(
    resume_schema_dict: dict[str, Any], analysis_dict: dict[str, Any]
) -> dict[str, Any]:
    """Stage 3: synthesize the PortfolioSchema from resume + analysis."""
    from src.ai.analysis_schema import AIAnalysisSchema
    from src.schemas.resume import ResumeSchema

    resume_schema = ResumeSchema.model_validate(resume_schema_dict)
    analysis_schema = AIAnalysisSchema.model_validate(analysis_dict)

    try:
        portfolio = portfolio_generator.generate(
            resume_schema,
            analysis_schema,
            model=settings.OLLAMA_MODEL,
            host=settings.OLLAMA_HOST,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
    except portfolio_exceptions.PortfolioError as exc:
        raise GeneratorServiceError(
            "portfolio_generation", _friendly_message(exc), original=exc
        ) from exc
    except ai_exceptions.AIError as exc:
        raise GeneratorServiceError(
            "portfolio_generation", _friendly_message(exc), original=exc
        ) from exc
    return portfolio.model_dump(mode="json")


def render_theme_preview(portfolio_dict: dict[str, Any], theme_value: str) -> dict[str, str]:
    """Stage 4 (preview mode): render a theme's HTML/CSS in memory without
    writing anything to disk — this backs the "live preview cards for
    every theme" requirement in Step 3.
    """
    from src.portfolio.portfolio_schema import PortfolioSchema

    if theme_value not in VALID_THEME_VALUES:
        raise GeneratorServiceError("website_generation", f"Unknown theme: '{theme_value}'")

    portfolio = PortfolioSchema.model_validate(portfolio_dict)
    theme = TemplateTheme(theme_value)

    try:
        schema = build_website_schema(portfolio, theme=theme)
        files = _strip_internal_render_fields(render(schema))
    except website_exceptions.WebsiteError as exc:
        raise GeneratorServiceError(
            "website_generation", _friendly_message(exc), original=exc
        ) from exc
    return files


def render_theme_to_directory(
    portfolio_dict: dict[str, Any], theme_value: str, output_dir: Path
) -> Path:
    """Stage 4 (export mode): render a theme and write it to *output_dir*,
    for website preview and ZIP-download flows.
    """
    from src.portfolio.portfolio_schema import PortfolioSchema
    from src.website.website_generator import generate as engine_generate

    if theme_value not in VALID_THEME_VALUES:
        raise GeneratorServiceError("website_generation", f"Unknown theme: '{theme_value}'")

    portfolio = PortfolioSchema.model_validate(portfolio_dict)
    theme = TemplateTheme(theme_value)

    try:
        generated_dir = engine_generate(portfolio, output_dir, theme=theme)
        _strip_internal_portfolio_data(generated_dir / "portfolio_data.json")
        return generated_dir
    except website_exceptions.WebsiteError as exc:
        raise GeneratorServiceError(
            "website_generation", _friendly_message(exc), original=exc
        ) from exc


def _strip_internal_render_fields(files: dict[str, str]) -> dict[str, str]:
    data = files.get("portfolio_data.json")
    if data:
        try:
            payload = json.loads(data)
            payload.pop("llm_model", None)
            files["portfolio_data.json"] = json.dumps(payload, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not sanitize rendered portfolio_data.json")
    return files


def _strip_internal_portfolio_data(path: Path) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.pop("llm_model", None)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError):
        logger.warning("Could not sanitize generated portfolio_data.json at %s", path)
