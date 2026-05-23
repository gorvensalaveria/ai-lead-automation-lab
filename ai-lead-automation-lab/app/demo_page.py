"""HTML template loader for the browser-based lead intake demo."""

from pathlib import Path


DEMO_TEMPLATE_PATH = Path(__file__).parent / "templates" / "demo.html"


def render_demo_page() -> str:
    """Return the web demo page HTML."""
    return DEMO_TEMPLATE_PATH.read_text(encoding="utf-8")
