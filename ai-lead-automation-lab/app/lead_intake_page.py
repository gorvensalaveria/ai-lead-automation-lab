"""HTML template loader for the browser-based lead intake workspace."""

from pathlib import Path


LEAD_INTAKE_TEMPLATE_PATH = Path(__file__).parent / "templates" / "lead_intake.html"


def render_lead_intake_page() -> str:
    """Return the lead intake page HTML."""
    return LEAD_INTAKE_TEMPLATE_PATH.read_text(encoding="utf-8")
