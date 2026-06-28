"""Regenerate real theme preview screenshots for the frontend.

Renders the real website-generator engine against the existing test fixture
(tests/website/fixtures/valid_portfolio.json) for every catalog theme, then
screenshots each rendered page with Playwright. Output lands in
frontend/public/theme-previews/<theme>.png — these are genuine generated
output, not mockups or fabricated images.

Usage (from website-generator/):
    pip install playwright --break-system-packages
    python -m playwright install chromium
    python scripts/generate_theme_previews.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.website.website_generator import generate_from_json
from src.website.website_schema import TemplateTheme

FIXTURE = Path(__file__).resolve().parent.parent / "tests/website/fixtures/valid_portfolio.json"
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "frontend/public/theme-previews"
VIEWPORT = {"width": 1440, "height": 960}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
            for theme in TemplateTheme:
                site_dir = generate_from_json(
                    portfolio_json_path=FIXTURE,
                    output_dir=str(Path(tmp) / theme.value),
                    theme=theme,
                )
                page.goto(f"file://{Path(site_dir) / 'index.html'}")
                page.wait_for_timeout(300)
                target = OUT_DIR / f"{theme.value}.png"
                page.screenshot(path=str(target))
                print(f"  ✓ {theme.value} -> {target}")
            browser.close()


if __name__ == "__main__":
    main()
