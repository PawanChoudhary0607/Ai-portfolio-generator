# ─────────────────────────────────────────────────────────
# AI Portfolio Generator — Application Entry Point
#
# CLI usage:
#   python main.py analyze <path/to/resume.pdf>
#   python main.py analyze <path/to/resume.pdf> --model qwen3:8b
#   python main.py analyze <path/to/resume.pdf> --model llama3 --host http://localhost:11434
#   python main.py portfolio <path/to/resume.pdf>
#   python main.py portfolio <path/to/resume.pdf> --model qwen3:14b
#
# ─────────────────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the full PDF → ResumeSchema → AIAnalysisSchema pipeline."""
    from src.ai.analyzer import analyze_and_save
    from src.ai.exceptions import AIError
    from src.extraction.exceptions import ExtractionError
    from src.extraction.pdf_extractor import read_pdf, build_output
    from src.extraction.validator import validate_input_path, validate_output_dir
    from src.parsing.resume_parser import parse

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    model = args.model
    host = args.host

    print(f"\n{'─' * 50}")
    print(f"  AI Portfolio Generator — Resume Analyzer")
    print(f"{'─' * 50}")
    print(f"  PDF      : {pdf_path}")
    print(f"  Model    : {model}")
    print(f"  Ollama   : {host}")
    print(f"  Output   : {output_dir}")
    print(f"{'─' * 50}\n")

    # Step 1 — Extract
    try:
        print("Step 1/3  Extracting PDF...")
        validated_pdf = validate_input_path(pdf_path)
        validated_dir = validate_output_dir(output_dir)
        page_count, raw_text = read_pdf(validated_pdf)
        payload = build_output(validated_pdf.name, page_count, raw_text)
        resume = parse(raw_text, filename=validated_pdf.name, page_count=page_count)
        print(f"          ✓ Extracted {page_count} page(s), {len(raw_text)} chars")
    except ExtractionError as e:
        print(f"\n  ✗ Extraction failed: {e}")
        return 1

    # Step 2 — Save ResumeSchema JSON
    resume_json_path = validated_dir / f"{validated_pdf.stem}.json"
    resume_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"          ✓ Resume JSON saved: {resume_json_path}")

    # Step 3 — Analyze
    try:
        print(f"\nStep 2/3  Sending to '{model}' via Ollama...")
        print("          (This may take 30–120 seconds on first run)")
        analysis_path = analyze_and_save(
            resume,
            output_dir=validated_dir,
            model=model,
            host=host,
        )
        print(f"          ✓ Analysis complete")
    except AIError as e:
        print(f"\n  ✗ AI analysis failed: {e}")
        print("\n  Troubleshooting:")
        print("    • Is Ollama running?  →  ollama serve")
        print(f"    • Is the model pulled?  →  ollama pull {model}")
        return 1

    # Step 4 — Report
    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    print(f"\nStep 3/3  Results")
    print(f"{'─' * 50}")
    print(f"  Strengths        : {len(data['strengths'])} identified")
    print(f"  Weaknesses       : {len(data['weaknesses'])} identified")
    print(f"  Missing skills   : {len(data['missing_skills'])} identified")
    print(f"  Career paths     : {len(data['recommended_career_paths'])} recommended")
    print(f"  Projects         : {len(data['recommended_projects'])} recommended")
    print(f"\n  Summary:\n  {data['summary'][:200]}...")
    print(f"\n  Full analysis saved to: {analysis_path}")
    print(f"{'─' * 50}\n")

    return 0


def cmd_portfolio(args: argparse.Namespace) -> int:
    """Run the full PDF → ResumeSchema → AIAnalysisSchema → PortfolioSchema pipeline."""
    from src.ai.analyzer import analyze
    from src.ai.exceptions import AIError
    from src.extraction.exceptions import ExtractionError
    from src.extraction.pdf_extractor import read_pdf, build_output
    from src.extraction.validator import validate_input_path, validate_output_dir
    from src.parsing.resume_parser import parse
    from src.portfolio.exceptions import PortfolioError
    from src.portfolio.portfolio_generator import generate_and_save

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    model = args.model
    host = args.host

    print(f"\n{'─' * 50}")
    print(f"  AI Portfolio Generator — Portfolio Builder")
    print(f"{'─' * 50}")
    print(f"  PDF      : {pdf_path}")
    print(f"  Model    : {model}")
    print(f"  Ollama   : {host}")
    print(f"  Output   : {output_dir}")
    print(f"{'─' * 50}\n")

    # Step 1 — Extract
    try:
        print("Step 1/3  Extracting PDF...")
        validated_pdf = validate_input_path(pdf_path)
        validated_dir = validate_output_dir(output_dir)
        page_count, raw_text = read_pdf(validated_pdf)
        resume = parse(raw_text, filename=validated_pdf.name, page_count=page_count)
        print(f"          ✓ Extracted {page_count} page(s), {len(raw_text)} chars")
    except ExtractionError as e:
        print(f"\n  ✗ Extraction failed: {e}")
        return 1

    # Step 2 — AI Analysis
    try:
        print(f"\nStep 2/3  Running AI analysis with '{model}'...")
        print("          (This may take 30–120 seconds on first run)")
        analysis = analyze(resume, model=model, host=host)
        print(f"          ✓ Analysis complete — {len(analysis.strengths)} strengths identified")
    except AIError as e:
        print(f"\n  ✗ AI analysis failed: {e}")
        print("\n  Troubleshooting:")
        print("    • Is Ollama running?  →  ollama serve")
        print(f"    • Is the model pulled?  →  ollama pull {model}")
        return 1

    # Step 3 — Generate Portfolio
    try:
        print(f"\nStep 3/3  Generating portfolio...")
        portfolio_path = generate_and_save(
            resume,
            analysis,
            output_dir=validated_dir,
            model=model,
            host=host,
        )
        print(f"          ✓ Portfolio generated")
    except (AIError, PortfolioError) as e:
        print(f"\n  ✗ Portfolio generation failed: {e}")
        return 1

    # Report
    import json as _json
    data = _json.loads(portfolio_path.read_text(encoding="utf-8"))
    print(f"\n{'─' * 50}")
    print(f"  Name           : {data['hero']['name']}")
    print(f"  Role           : {data['hero']['role']}")
    print(f"  Skills         : {len(data['skills'])} listed")
    print(f"  Projects       : {len(data['projects'])} recommended")
    print(f"  Career paths   : {len(data['career_paths'])} suggested")
    print(f"\n  Headline:\n  {data['hero']['headline']}")
    print(f"\n  Portfolio saved to: {portfolio_path}")
    print(f"{'─' * 50}\n")

    return 0


def cmd_website(args: argparse.Namespace) -> int:
    """Run the full PDF → Website pipeline (Milestone 5).

    Accepts either:
      • a PDF path  → runs full pipeline, then generates the website
      • a JSON path → loads an existing PortfolioSchema JSON, skips LLM steps
    """
    from src.website.exceptions import WebsiteError
    from src.website.website_generator import generate, generate_from_json
    from src.website.website_schema import TemplateTheme

    # Resolve theme
    try:
        theme = TemplateTheme(args.theme)
    except ValueError:
        valid = [t.value for t in TemplateTheme]
        print(f"\n  ✗ Unknown theme '{args.theme}'. Valid choices: {valid}")
        return 1

    input_path = Path(args.pdf)
    suffix = input_path.suffix.lower()

    print(f"\n{'─' * 50}")
    print(f"  AI Portfolio Generator — Website Builder")
    print(f"{'─' * 50}")
    print(f"  Input    : {input_path}")
    print(f"  Theme    : {theme.value}")
    print(f"{'─' * 50}\n")

    # ── Fast path: JSON input ────────────────────────────────────────────────
    if suffix == ".json":
        print("Step 1/1  Generating website from portfolio JSON...")
        try:
            site_dir = generate_from_json(
                portfolio_json_path=input_path,
                output_dir=args.output_dir,
                theme=theme,
            )
        except WebsiteError as e:
            print(f"\n  ✗ Website generation failed: {e}")
            return 1
        _print_website_result(site_dir)
        return 0

    # ── Full pipeline: PDF input ─────────────────────────────────────────────
    from src.ai.analyzer import analyze
    from src.ai.exceptions import AIError
    from src.extraction.exceptions import ExtractionError
    from src.extraction.pdf_extractor import read_pdf
    from src.extraction.validator import validate_input_path, validate_output_dir
    from src.parsing.resume_parser import parse
    from src.portfolio.exceptions import PortfolioError
    from src.portfolio.portfolio_generator import generate as generate_portfolio

    model = args.model
    host = args.host

    print(f"  Model    : {model}")
    print(f"  Ollama   : {host}\n")

    # Step 1 — Extract PDF
    try:
        print("Step 1/4  Extracting PDF...")
        validated_pdf = validate_input_path(input_path)
        intermediate_dir = validate_output_dir(Path("data/processed"))
        page_count, raw_text = read_pdf(validated_pdf)
        resume = parse(raw_text, filename=validated_pdf.name, page_count=page_count)
        print(f"          ✓ Extracted {page_count} page(s), {len(raw_text)} chars")
    except ExtractionError as e:
        print(f"\n  ✗ Extraction failed: {e}")
        return 1

    # Step 2 — AI Analysis
    try:
        print(f"\nStep 2/4  Running AI analysis with '{model}'...")
        analysis = analyze(resume, model=model, host=host)
        print(f"          ✓ Analysis complete — {len(analysis.strengths)} strengths")
    except AIError as e:
        print(f"\n  ✗ AI analysis failed: {e}")
        print("    • Is Ollama running?  →  ollama serve")
        print(f"    • Is the model pulled?  →  ollama pull {model}")
        return 1

    # Step 3 — Generate Portfolio
    try:
        print(f"\nStep 3/4  Generating portfolio content...")
        portfolio = generate_portfolio(resume, analysis, model=model, host=host)
        print(f"          ✓ Portfolio built — {len(portfolio.skills)} skills")
    except (AIError, PortfolioError) as e:
        print(f"\n  ✗ Portfolio generation failed: {e}")
        return 1

    # Step 4 — Build Website
    try:
        print(f"\nStep 4/4  Building website (theme: {theme.value})...")
        output_dir = args.output_dir
        if output_dir is None:
            stem = validated_pdf.stem
            output_dir = f"data/output/{stem}_portfolio_site"
        site_dir = generate(portfolio, output_dir=output_dir, theme=theme)
        print(f"          ✓ Website generated")
    except WebsiteError as e:
        print(f"\n  ✗ Website generation failed: {e}")
        return 1

    _print_website_result(site_dir)
    return 0


def _print_website_result(site_dir: Path) -> None:
    """Print final summary for the website command."""
    files = [f.name for f in site_dir.iterdir() if f.is_file()]
    print(f"\n{'─' * 50}")
    print(f"  Website output: {site_dir}")
    print(f"  Files generated:")
    for f in sorted(files):
        size = (site_dir / f).stat().st_size
        print(f"    • {f}  ({size:,} bytes)")
    print(f"\n  Open in browser:")
    print(f"    file://{site_dir}/index.html")
    print(f"{'─' * 50}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="AI Portfolio Generator — CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Extract and analyze a resume PDF",
    )
    analyze_parser.add_argument(
        "pdf",
        help="Path to the resume PDF file",
    )
    analyze_parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    analyze_parser.add_argument(
        "--host",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    analyze_parser.add_argument(
        "--output-dir",
        default="data/processed",
        dest="output_dir",
        help="Output directory for JSON files (default: data/processed)",
    )

    portfolio_parser = subparsers.add_parser(
        "portfolio",
        help="Generate a portfolio JSON from a resume PDF (full pipeline)",
    )
    portfolio_parser.add_argument(
        "pdf",
        help="Path to the resume PDF file",
    )
    portfolio_parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    portfolio_parser.add_argument(
        "--host",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    portfolio_parser.add_argument(
        "--output-dir",
        default="data/processed",
        dest="output_dir",
        help="Output directory for JSON files (default: data/processed)",
    )

    website_parser = subparsers.add_parser(
        "website",
        help="Generate a static portfolio website (full pipeline or from JSON)",
    )
    website_parser.add_argument(
        "pdf",
        help="Path to the resume PDF or an existing *_portfolio.json file",
    )
    website_parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    website_parser.add_argument(
        "--host",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    website_parser.add_argument(
        "--theme",
        default="minimal-white-orange",
        choices=[
            "minimal-white-orange",
            "executive-black-gold",
            "developer-dark",
            "creative-portfolio",
            "modern-saas",
        ],
        help="Visual theme for the website (default: minimal-white-orange)",
    )
    website_parser.add_argument(
        "--output-dir",
        default=None,
        dest="output_dir",
        help="Output directory for the website (default: data/output/<stem>_portfolio_site)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        return cmd_analyze(args)

    if args.command == "portfolio":
        return cmd_portfolio(args)

    if args.command == "website":
        return cmd_website(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
