"""HTML renderer for the saved lead review history page."""

from html import escape
from typing import Any


def render_history_page(history_rows: list[dict[str, Any]]) -> str:
    """Return a browser page for reviewing saved processed leads."""
    rows_html = "\n".join(render_history_row(row) for row in history_rows)
    total = len(history_rows)
    empty_state = ""

    if not history_rows:
        empty_state = """
          <div class="history-empty">
            <h3>No processed leads yet</h3>
            <p>Process a lead from the demo page and it will appear here for review.</p>
            <a class="text-link" href="/demo">Open demo</a>
          </div>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lead Review History</title>
  <link rel="stylesheet" href="/static/demo.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>Lead Review History</h1>
        <p class="subtitle">Review saved lead qualification results and CRM-ready handoff fields.</p>
      </div>
      <nav class="header-actions" aria-label="Demo navigation">
        <a class="nav-link" href="/demo">Process Lead</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="value-strip" aria-label="History summary">
      <div class="value-item">
        <span>Saved Leads</span>
        <strong>{total}</strong>
        <p>Processed results found in local JSON output storage.</p>
      </div>
      <div class="value-item">
        <span>Review Queue</span>
        <strong>Human-ready</strong>
        <p>Summaries, scores, and next actions are ready for review.</p>
      </div>
      <div class="value-item">
        <span>Next Product Step</span>
        <strong>CSV export</strong>
        <p>This history view can later feed a spreadsheet or CRM export.</p>
      </div>
    </section>

    <section class="panel history-panel" aria-labelledby="history-title">
      <div class="panel-title">
        <div>
          <h2 id="history-title">Processed Lead History</h2>
          <p class="helper-text">Most recent saved outputs appear first.</p>
        </div>
      </div>
      {empty_state}
      <div class="table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>Processed</th>
              <th>Contact</th>
              <th>Company</th>
              <th>Classification</th>
              <th>Score</th>
              <th>Rating</th>
              <th>Next Action</th>
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <footer>
    Demo built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
</body>
</html>
"""


def render_history_row(row: dict[str, Any]) -> str:
    """Return one table row for a saved processed lead."""
    classification = str(row.get("classification", "")).lower()
    if classification not in {"hot", "warm", "cold"}:
        classification = "cold"

    score = format_score(row.get("lead_score", ""), row.get("max_score", ""))

    return f"""
            <tr>
              <td>{escape(str(row.get("processed_at", "")))}</td>
              <td>{escape(str(row.get("contact_name", "")))}</td>
              <td>{escape(str(row.get("company", "")))}</td>
              <td><span class="badge {classification}">{escape(classification)}</span></td>
              <td>{escape(score)}</td>
              <td>{escape(str(row.get("lead_rating", "")))}</td>
              <td>{escape(str(row.get("recommended_next_action", "")))}</td>
              <td><code>{escape(str(row.get("file_name", "")))}</code></td>
            </tr>
    """


def format_score(lead_score: Any, max_score: Any) -> str:
    """Format score values for the history table."""
    if lead_score == "" and max_score == "":
        return ""

    return f"{lead_score}/{max_score}"
