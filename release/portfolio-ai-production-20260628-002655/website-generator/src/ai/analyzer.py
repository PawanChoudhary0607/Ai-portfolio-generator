"""Resume analysis orchestrator.

Pipeline:
    ResumeSchema → Prompt Builder → Ollama Client → Validators → AIAnalysisSchema

This module owns the pipeline. It never parses JSON directly and never
calls Ollama directly — those concerns belong to validators.py and ollama_client.py.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.ai.analysis_schema import AIAnalysisSchema
from src.ai.ollama_client import OllamaClient
from src.ai.prompts import build_prompt
from src.ai.validators import parse_and_validate
from src.schemas.resume import ResumeSchema

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen3:8b"
DEFAULT_OUTPUT_DIR = "data/processed"


def analyze(
    resume: ResumeSchema,
    model: str = DEFAULT_MODEL,
    host: str = "http://localhost:11434",
    timeout: int = 120,
) -> AIAnalysisSchema:
    """Analyze a parsed resume using a local Ollama model.

    Args:
        resume:  Validated ResumeSchema from Milestone 2 pipeline.
        model:   Ollama model name. Default: qwen3:8b.
        host:    Ollama server URL.
        timeout: Request timeout in seconds.

    Returns:
        Validated AIAnalysisSchema.

    Raises:
        OllamaUnavailableError, ModelNotFoundError, OllamaTimeoutError,
        MalformedResponseError, SchemaValidationError — all from src.ai.exceptions.
    """
    client = OllamaClient(model=model, host=host, timeout=timeout)
    prompt = build_prompt(resume)

    logger.info("Analyzing resume for: %s", resume.personal.name if resume.personal else "unknown")

    raw_response = client.generate(prompt)
    result = parse_and_validate(raw_response, model_used=model)

    logger.info("Analysis complete — %d strengths, %d career paths",
                len(result.strengths), len(result.recommended_career_paths))

    return result


def analyze_and_save(
    resume: ResumeSchema,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    model: str = DEFAULT_MODEL,
    host: str = "http://localhost:11434",
    timeout: int = 120,
) -> Path:
    """Analyze a resume and save AIAnalysisSchema as JSON.

    Returns the path of the written JSON file.
    """
    result = analyze(resume, model=model, host=host, timeout=timeout)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(resume.filename).stem if resume.filename else "resume"
    output_path = output_dir / f"{stem}_analysis.json"

    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    logger.info("Saved analysis to: %s", output_path)
    return output_path
