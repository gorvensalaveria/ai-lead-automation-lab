"""HTML renderer for the saved lead review history page."""

import json
from html import escape
from math import ceil
from typing import Any
from urllib.parse import quote


HISTORY_PAGE_SIZE = 5
VALID_HISTORY_FILTERS = {"all", "hot", "warm", "cold"}


def render_history_page(
    history_rows: list[dict[str, Any]],
    selected_classification: str = "all",
    page: int = 1,
) -> str:
    """Return a browser page for reviewing saved processed leads."""
    selected_classification = normalize_history_filter(selected_classification)
    counts = get_history_counts(history_rows)
    filtered_rows = filter_history_rows(history_rows, selected_classification)
    page_rows, current_page, total_pages = paginate_history_rows(
        filtered_rows,
        page=page,
    )
    rows_html = "\n".join(render_history_row(row) for row in page_rows)
    total = len(history_rows)
    filtered_total = len(filtered_rows)
    empty_state = ""

    if not page_rows:
        empty_state = """
          <div class="history-empty">
            <h3>No processed leads yet</h3>
            <p>Process a lead from the demo page or change the filter to review saved results.</p>
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
          <p class="helper-text">Showing {len(page_rows)} of {filtered_total} matching saved outputs. Most recent appears first.</p>
        </div>
      </div>
      {render_history_filters(selected_classification, counts)}
      {empty_state}
      <div class="table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>Contact</th>
              <th>Company</th>
              <th>Classification</th>
              <th>Score</th>
              <th>Rating</th>
              <th>Processed</th>
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
      {render_pagination(
          selected_classification=selected_classification,
          current_page=current_page,
          total_pages=total_pages,
      )}
    </section>
  </main>

  <footer>
    Demo built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
</body>
</html>
"""


def render_history_detail_page(result: dict[str, Any], file_name: str) -> str:
    """Return a browser page for reviewing one saved processed lead."""
    lead = result.get("lead", {})
    contact = lead.get("contact", {})
    lead_details = lead.get("lead_details", {})
    ai_outputs = result.get("ai_outputs", {})
    crm_ready = result.get("crm_ready", {})
    score = ai_outputs.get("score", {})
    breakdown = score.get("breakdown", {})
    classification = normalize_detail_classification(
        crm_ready.get("classification", ai_outputs.get("classification", ""))
    )
    contact_name = crm_ready.get("contact_name") or (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    )
    company = crm_ready.get("company", contact.get("company", ""))
    service_interest = crm_ready.get(
        "service_interest",
        lead_details.get("service_interest", ""),
    )
    total_score = crm_ready.get("lead_score", score.get("total_score", ""))
    max_score = crm_ready.get("max_score", score.get("max_score", ""))
    lead_rating = crm_ready.get("lead_rating", score.get("rating", ""))
    recommended_next_action = crm_ready.get("recommended_next_action", "")
    summary = crm_ready.get("summary", ai_outputs.get("summary", ""))
    follow_up_message = crm_ready.get(
        "follow_up_message",
        ai_outputs.get("follow_up_message", ""),
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lead Detail - {escape(contact_name or file_name)}</title>
  <link rel="stylesheet" href="/static/demo.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>Lead Detail Review</h1>
        <p class="subtitle">Review one saved lead qualification result and CRM-ready handoff.</p>
      </div>
      <nav class="header-actions" aria-label="History navigation">
        <a class="nav-link" href="/history">Back to History</a>
        <a class="nav-link" href="/demo">Process Lead</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="panel detail-panel" aria-labelledby="detail-title">
      <div class="detail-header">
        <div>
          <p class="eyebrow">Saved Result</p>
          <h2 id="detail-title">{escape(contact_name or "Unknown contact")} at {escape(company or "Unknown company")}</h2>
          <p class="helper-text">{escape(service_interest)}</p>
        </div>
        <div class="score-lockup">
          <strong>{escape(format_score(total_score, max_score))}</strong>
          <span>{escape(str(lead_rating))}</span>
        </div>
      </div>

      <div class="detail-metrics">
        <div class="classification-card {classification}">
          <span>Classification</span>
          <strong class="badge {classification}">{escape(classification)}</strong>
        </div>
        <div>
          <span>Processed</span>
          <strong>{escape(str(crm_ready.get("processed_at", result.get("processed_at", ""))))}</strong>
        </div>
        <div>
          <span>Source</span>
          <strong>{escape(str(crm_ready.get("source", lead.get("source", ""))))}</strong>
        </div>
      </div>

      <section class="detail-section" aria-labelledby="next-action-title">
        <h3 id="next-action-title">Recommended Next Action</h3>
        <p>{escape(str(recommended_next_action))}</p>
      </section>

      <section class="detail-section" aria-labelledby="summary-title">
        <h3 id="summary-title">AI Summary</h3>
        <p>{escape(str(summary))}</p>
      </section>

      <section class="detail-section" aria-labelledby="breakdown-title">
        <h3 id="breakdown-title">Score Breakdown</h3>
        <div class="breakdown">
          <div>Fit: {escape(str(breakdown.get("fit", "")))}</div>
          <div>Urgency: {escape(str(breakdown.get("urgency", "")))}</div>
          <div>Budget: {escape(str(breakdown.get("budget", "")))}</div>
          <div>Intent: {escape(str(breakdown.get("intent", "")))}</div>
        </div>
      </section>

      <section class="detail-section" aria-labelledby="follow-up-title">
        <h3 id="follow-up-title">Follow-Up Draft</h3>
        <div class="message-box">{escape(str(follow_up_message))}</div>
      </section>

      <section class="detail-section" aria-labelledby="crm-title">
        <h3 id="crm-title">CRM-Ready Fields</h3>
        <div class="crm-grid">
          {render_crm_field("Lead ID", crm_ready.get("lead_id", lead.get("lead_id", "")))}
          {render_crm_field("Contact", contact_name)}
          {render_crm_field("Email", crm_ready.get("email", contact.get("email", "")))}
          {render_crm_field("Phone", crm_ready.get("phone", contact.get("phone", "")))}
          {render_crm_field("Company", company)}
          {render_crm_field("Business Type", crm_ready.get("business_type", lead.get("business_type", "")))}
          {render_crm_field("Service Interest", service_interest)}
          {render_crm_field("Preferred Contact", crm_ready.get("preferred_contact_method", lead_details.get("preferred_contact_method", "")))}
        </div>
      </section>

      <section class="detail-section" aria-labelledby="source-title">
        <h3 id="source-title">Saved Output File</h3>
        <p><code>{escape(file_name)}</code></p>
        <details class="json-details">
          <summary>View saved JSON</summary>
          <pre class="json-box">{escape(json.dumps(result, indent=2))}</pre>
        </details>
      </section>
    </section>
  </main>

  <footer>
    Demo built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
</body>
</html>
"""


def normalize_history_filter(value: str) -> str:
    """Return a supported history classification filter."""
    normalized = (value or "all").lower()
    if normalized not in VALID_HISTORY_FILTERS:
        return "all"

    return normalized


def filter_history_rows(
    history_rows: list[dict[str, Any]],
    selected_classification: str,
) -> list[dict[str, Any]]:
    """Return history rows that match the selected classification filter."""
    if selected_classification == "all":
        return history_rows

    return [
        row
        for row in history_rows
        if str(row.get("classification", "")).lower() == selected_classification
    ]


def paginate_history_rows(
    history_rows: list[dict[str, Any]],
    page: int,
    page_size: int = HISTORY_PAGE_SIZE,
) -> tuple[list[dict[str, Any]], int, int]:
    """Return one page of history rows plus pagination metadata."""
    total_pages = max(1, ceil(len(history_rows) / page_size))
    current_page = min(max(page, 1), total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size

    return history_rows[start:end], current_page, total_pages


def get_history_counts(history_rows: list[dict[str, Any]]) -> dict[str, int]:
    """Return all/hot/warm/cold counts for the history filters."""
    counts = {"all": len(history_rows), "hot": 0, "warm": 0, "cold": 0}

    for row in history_rows:
        classification = str(row.get("classification", "")).lower()
        if classification in {"hot", "warm", "cold"}:
            counts[classification] += 1

    return counts


def render_history_filters(
    selected_classification: str,
    counts: dict[str, int],
) -> str:
    """Return classification filter links for the history page."""
    filter_links = []
    labels = {
        "all": "All",
        "hot": "Hot",
        "warm": "Warm",
        "cold": "Cold",
    }

    for value, label in labels.items():
        active_class = "active" if value == selected_classification else ""
        aria_current = ' aria-current="page"' if active_class else ""
        filter_links.append(
            f"""
            <a class="history-filter-link {active_class}" href="{build_history_url(value, 1)}"{aria_current}>
              <span class="filter-label">{label}</span>
              <span class="filter-count">{counts.get(value, 0)}</span>
            </a>
            """
        )

    return f"""
      <div class="history-toolbar">
        <div>
          <p class="toolbar-label">Filter by classification</p>
          <div class="history-filters" aria-label="Lead classification filters">
            {"".join(filter_links)}
          </div>
        </div>
      </div>
    """


def render_pagination(
    selected_classification: str,
    current_page: int,
    total_pages: int,
) -> str:
    """Return numbered pagination controls."""
    if total_pages <= 1:
        return ""

    page_links = []
    previous_page = max(current_page - 1, 1)
    next_page = min(current_page + 1, total_pages)
    previous_class = "disabled" if current_page == 1 else ""
    next_class = "disabled" if current_page == total_pages else ""

    for page_number in range(1, total_pages + 1):
        active_class = "active" if page_number == current_page else ""
        aria_current = ' aria-current="page"' if active_class else ""
        page_links.append(
            f"""
            <a class="history-page-link {active_class}" href="{build_history_url(selected_classification, page_number)}"{aria_current}>
              {page_number}
            </a>
            """
        )

    return f"""
      <nav class="pagination" aria-label="History pagination">
        <span class="pagination-summary">Page {current_page} of {total_pages}</span>
        <div class="pagination-controls">
          <a class="history-page-link pagination-step {previous_class}" href="{build_history_url(selected_classification, previous_page)}">Previous</a>
          {"".join(page_links)}
          <a class="history-page-link pagination-step {next_class}" href="{build_history_url(selected_classification, next_page)}">Next</a>
        </div>
      </nav>
    """


def build_history_url(classification: str, page: int) -> str:
    """Build a history page URL for filters and pagination."""
    if classification == "all":
        return f"/history?page={page}"

    return f"/history?classification={classification}&page={page}"


def build_history_detail_url(file_name: str) -> str:
    """Build a lead detail URL for a saved output file."""
    return f"/history/{quote(file_name)}"


def render_history_row(row: dict[str, Any]) -> str:
    """Return one table row for a saved processed lead."""
    classification = str(row.get("classification", "")).lower()
    if classification not in {"hot", "warm", "cold"}:
        classification = "cold"

    score = format_score(row.get("lead_score", ""), row.get("max_score", ""))
    file_name = str(row.get("file_name", ""))
    detail_url = build_history_detail_url(file_name)

    return f"""
            <tr>
              <td><a class="row-link" href="{escape(detail_url)}">{escape(str(row.get("contact_name", "")))}</a></td>
              <td>{escape(str(row.get("company", "")))}</td>
              <td><span class="badge {classification}">{escape(classification)}</span></td>
              <td>{escape(score)}</td>
              <td>{escape(str(row.get("lead_rating", "")))}</td>
              <td>{escape(str(row.get("processed_at", "")))}</td>
              <td><a class="file-link" href="{escape(detail_url)}"><code>{escape(file_name)}</code></a></td>
            </tr>
    """


def normalize_detail_classification(classification: Any) -> str:
    """Return a valid CSS class for one lead classification."""
    normalized = str(classification).lower()
    if normalized in {"hot", "warm", "cold"}:
        return normalized

    return "cold"


def render_crm_field(label: str, value: Any) -> str:
    """Return one CRM-ready field block."""
    return f"""
          <div>
            <span>{escape(label)}</span>
            {escape(str(value))}
          </div>
    """


def format_score(lead_score: Any, max_score: Any) -> str:
    """Format score values for the history table."""
    if lead_score == "" and max_score == "":
        return ""

    return f"{lead_score}/{max_score}"
