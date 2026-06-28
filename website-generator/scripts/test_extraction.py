"""Manual smoke-test script: extract a sample PDF and print the result.

Usage:
    python scripts/test_extraction.py data/raw/sample.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.extraction.pdf_extractor import extract


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_extraction.py <path/to/file.pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    print(f"Extracting: {pdf_path}")

    output_path = extract(pdf_path, output_dir="data/processed")
    data = json.loads(output_path.read_text(encoding="utf-8"))

    print(f"\nOutput saved to: {output_path}")
    print(f"  filename   : {data['filename']}")
    print(f"  page_count : {data['page_count']}")
    print(f"  text_length: {len(data['raw_text'])} chars")
    print(f"  preview    : {data['raw_text'][:120].strip()!r}")


if __name__ == "__main__":
    main()
