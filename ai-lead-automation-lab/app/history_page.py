"""HTML renderer for the saved lead review history page."""

import json
from datetime import datetime
from html import escape
from math import ceil
from typing import Any
from urllib.parse import quote

from app.privacy import mask_lead_result


HISTORY_PAGE_SIZE = 5
VALID_HISTORY_FILTERS = {"all", "hot", "warm", "cold"}
VALID_STATUS_FILTERS = {
    "all",
    "new",
    "reviewed",
    "contacted",
    "archived",
    "needs_follow_up",
}
VALID_HISTORY_SORTS = {"newest", "score_desc", "score_asc", "company", "status"}


def render_history_page(
    history_rows: list[dict[str, Any]],
    selected_classification: str = "all",
    selected_status: str = "all",
    selected_sort: str = "newest",
    search_query: str = "",
    page: int = 1,
) -> str:
    """Return a browser page for reviewing saved processed leads."""
    selected_classification = normalize_history_filter(selected_classification)
    selected_status = normalize_status_filter(selected_status)
    selected_sort = normalize_history_sort(selected_sort)
    search_query = str(search_query or "").strip()
    counts = get_history_counts(history_rows)
    status_counts = get_status_counts(history_rows)
    analytics = get_history_analytics(history_rows)
    filtered_rows = filter_history_rows(
        history_rows=history_rows,
        selected_classification=selected_classification,
        selected_status=selected_status,
        search_query=search_query,
    )
    filtered_rows = sort_history_rows(filtered_rows, selected_sort)
    page_rows, current_page, total_pages = paginate_history_rows(
        filtered_rows,
        page=page,
    )
    rows_html = "\n".join(render_history_row(row) for row in page_rows)
    filtered_total = len(filtered_rows)
    empty_state = ""

    if not page_rows:
        empty_state = """
          <div class="history-empty">
            <h3>No processed leads yet</h3>
            <p>Process a lead from the lead intake page or change the filter to review saved results.</p>
            <a class="text-link" href="/lead-intake">Open lead intake</a>
          </div>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lead Review History</title>
  <link rel="stylesheet" href="/static/lead-intake.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>Lead Review History</h1>
        <p class="subtitle">Review saved lead qualification results and CRM-ready handoff fields.</p>
      </div>
      <nav class="header-actions" aria-label="Lead intake navigation">
        <a class="nav-link" href="/lead-intake">Process Lead</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="value-strip" aria-label="History summary">
      <div class="value-item">
        <span>Saved Leads</span>
        <strong>{analytics["total"]}</strong>
        <p>Processed leads indexed for review and export.</p>
      </div>
      <div class="value-item">
        <span>Hot Leads</span>
        <strong>{analytics["hot"]}</strong>
        <p>Highest-priority leads ready for fast follow-up.</p>
      </div>
      <div class="value-item">
        <span>Average Score</span>
        <strong>{analytics["average_score"]}</strong>
        <p>Average quality score across saved lead history.</p>
      </div>
      <div class="value-item">
        <span>New Reviews</span>
        <strong>{analytics["new"]}</strong>
        <p>Leads still waiting for human review.</p>
      </div>
    </section>

    <section class="panel history-panel" aria-labelledby="history-title">
      <div class="panel-title">
        <div>
          <h2 id="history-title">Processed Lead History</h2>
          <p class="helper-text">Showing {len(page_rows)} of {filtered_total} matching saved outputs. Most recent appears first.</p>
        </div>
        <a class="detail-link" href="/history/export.csv">Export CSV</a>
      </div>
      {render_history_filters(selected_classification, counts)}
      {render_history_controls(
          selected_classification=selected_classification,
          selected_status=selected_status,
          selected_sort=selected_sort,
          search_query=search_query,
          status_counts=status_counts,
      )}
      {empty_state}
      {render_bulk_actions() if page_rows else ""}
      <div class="table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th><input type="checkbox" data-select-all-leads aria-label="Select all leads on this page"></th>
              <th>Contact</th>
              <th>Company</th>
              <th>Classification</th>
              <th>Score</th>
              <th>Rating</th>
              <th>Status</th>
              <th>Processed</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
      {render_pagination(
          selected_classification=selected_classification,
          selected_status=selected_status,
          selected_sort=selected_sort,
          search_query=search_query,
          current_page=current_page,
          total_pages=total_pages,
      )}
    </section>
  </main>

  <footer>
    Built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
  <script>
    const selectAll = document.querySelector("[data-select-all-leads]");
    const bulkMessage = document.querySelector("[data-bulk-message]");
    const bulkStatus = document.querySelector("[data-bulk-status]");

    function selectedLeadCheckboxes() {{
      return Array.from(document.querySelectorAll("[data-lead-checkbox]:checked"));
    }}

    if (selectAll) {{
      selectAll.addEventListener("change", () => {{
        document.querySelectorAll("[data-lead-checkbox]").forEach((checkbox) => {{
          checkbox.checked = selectAll.checked;
        }});
      }});
    }}

    document.querySelectorAll("[data-bulk-action]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const checkedBoxes = selectedLeadCheckboxes();
        const reviewStatus = button.dataset.bulkAction === "archive"
          ? "archived"
          : bulkStatus?.value;

        if (!checkedBoxes.length) {{
          bulkMessage.textContent = "Select at least one lead first.";
          return;
        }}

        if (!reviewStatus) {{
          bulkMessage.textContent = "Choose a status first.";
          return;
        }}

        button.disabled = true;
        bulkMessage.textContent = "Updating selected leads...";

        try {{
          const response = await fetch("/api/history/bulk-status", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{
              file_names: checkedBoxes.map((checkbox) => checkbox.value),
              review_status: reviewStatus
            }})
          }});
          const data = await response.json();

          if (!response.ok) {{
            throw new Error(data.detail || "Unable to update selected leads.");
          }}

          data.updated.forEach((row) => {{
            const checkbox = document.querySelector(`[data-lead-checkbox][value="${{CSS.escape(row.file_name)}}"]`);
            const tableRow = checkbox?.closest("tr");
            const statusCell = tableRow?.querySelector("[data-row-status]");
            if (statusCell) {{
              statusCell.textContent = row.review_status.replaceAll("_", " ");
              statusCell.className = `status-pill ${{row.review_status}}`;
            }}
          }});

          checkedBoxes.forEach((checkbox) => {{
            checkbox.checked = false;
          }});
          if (selectAll) {{
            selectAll.checked = false;
          }}

          const errorText = data.errors.length ? ` ${{data.errors.length}} failed.` : "";
          bulkMessage.textContent = `${{data.updated.length}} lead(s) updated.${{errorText}}`;
        }} catch (error) {{
          bulkMessage.textContent = error.message;
        }} finally {{
          button.disabled = false;
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def render_history_detail_page(
    result: dict[str, Any],
    file_name: str,
    events: list[dict[str, Any]] | None = None,
    masked: bool = False,
) -> str:
    """Return a browser page for reviewing one saved processed lead."""
    display_result = mask_lead_result(result) if masked else result
    privacy_toggle_href = (
        build_history_detail_url(file_name)
        if masked
        else f"{build_history_detail_url(file_name)}?privacy=masked"
    )
    privacy_toggle_label = "Show Original Contact Data" if masked else "Mask Contact Data"
    privacy_state = "Masked" if masked else "Visible"

    lead = display_result.get("lead", {})
    contact = lead.get("contact", {})
    lead_details = lead.get("lead_details", {})
    ai_outputs = display_result.get("ai_outputs", {})
    crm_ready = display_result.get("crm_ready", {})
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
    processed_at = crm_ready.get("processed_at", display_result.get("processed_at", ""))
    source = crm_ready.get("source", lead.get("source", ""))
    review_status = crm_ready.get("review_status", display_result.get("review_status", "new"))
    recommended_next_action = crm_ready.get("recommended_next_action", "")
    summary = crm_ready.get("summary", ai_outputs.get("summary", ""))
    follow_up_message = crm_ready.get(
        "follow_up_message",
        ai_outputs.get("follow_up_message", ""),
    )
    ai_metadata = get_ai_metadata(display_result)
    activity_timeline = render_activity_timeline(events or [])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lead Detail - {escape(contact_name or file_name)}</title>
  <link rel="stylesheet" href="/static/lead-intake.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>Lead Detail Review</h1>
        <p class="subtitle">Review a saved lead qualification result and CRM-ready handoff.</p>
      </div>
      <nav class="header-actions" aria-label="History navigation">
        <a class="nav-link" href="/history">Back to History</a>
        <a class="nav-link" href="/lead-intake">Process Lead</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="panel detail-panel" aria-labelledby="detail-title">
      <div class="detail-header">
        <div>
          <p class="detail-eyebrow">Saved Result</p>
          <h2 id="detail-title">{escape(contact_name or "Unknown contact")} at {escape(company or "Unknown company")}</h2>
          <p class="helper-text">{escape(service_interest)}</p>
        </div>
        <div class="score-lockup">
          <strong class="score-value {classification}">{escape(format_score(total_score, max_score))}</strong>
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
          <strong>{escape(format_datetime(processed_at))}</strong>
        </div>
        <div>
          <span>Source</span>
          <strong>{escape(format_display_label(source))}</strong>
        </div>
        <div>
          <span>Report Input</span>
          <strong>CSV Report</strong>
        </div>
        <div>
          <span>Review Status</span>
          <strong id="review-status-label">{escape(format_display_label(review_status))}</strong>
        </div>
        <div>
          <span>Privacy Mode</span>
          <strong>{privacy_state}</strong>
        </div>
      </div>

      <section class="detail-section" aria-labelledby="review-status-title">
        <h3 id="review-status-title">Review Workflow</h3>
        <div class="status-actions" data-status-file="{escape(file_name)}">
          <button class="status-button" type="button" data-review-status="new">New</button>
          <button class="status-button" type="button" data-review-status="reviewed">Reviewed</button>
          <button class="status-button" type="button" data-review-status="contacted">Contacted</button>
          <button class="status-button" type="button" data-review-status="needs_follow_up">Needs Follow-Up</button>
          <button class="status-button" type="button" data-review-status="archived">Archived</button>
          <button class="status-button danger" type="button" data-archive-lead="true">Archive Lead</button>
          <a class="secondary-link compact" href="{escape(privacy_toggle_href)}">{escape(privacy_toggle_label)}</a>
        </div>
        <p class="helper-text" id="review-status-message">Use this status to track the lead after human review. Privacy mode masks email and phone on this page.</p>
      </section>

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
        <div class="section-heading-row">
          <h3 id="follow-up-title">Follow-Up Draft</h3>
          <button class="copy-button" type="button" data-copy-target="follow-up-message">Copy Draft</button>
        </div>
        <div class="message-box" id="follow-up-message">{escape(str(follow_up_message))}</div>
      </section>

      <section class="detail-section" aria-labelledby="crm-title">
        <h3 id="crm-title">CRM-Ready Fields</h3>
        <div class="crm-grid">
          {render_crm_field("Lead ID", crm_ready.get("lead_id", lead.get("lead_id", "")))}
          {render_crm_field("Contact", contact_name)}
          {render_crm_field("Email", crm_ready.get("email", contact.get("email", "")))}
          {render_crm_field("Phone", crm_ready.get("phone", contact.get("phone", "")))}
          {render_crm_field("Company", company)}
          {render_crm_field("Business Type", format_display_label(crm_ready.get("business_type", lead.get("business_type", ""))))}
          {render_crm_field("Service Interest", service_interest)}
          {render_crm_field("Preferred Contact", format_display_label(crm_ready.get("preferred_contact_method", lead_details.get("preferred_contact_method", ""))))}
        </div>
      </section>

      <section class="detail-section" aria-labelledby="metadata-title">
        <h3 id="metadata-title">AI Processing Metadata</h3>
        <div class="crm-grid">
          {render_crm_field("Model", ai_metadata.get("model", ""))}
          {render_crm_field("Workflow Version", ai_metadata.get("workflow_version", ""))}
          {render_crm_field("Summary Prompt", ai_metadata.get("summary_prompt_version", ""))}
          {render_crm_field("Classification Prompt", ai_metadata.get("classification_prompt_version", ""))}
          {render_crm_field("Follow-Up Prompt", ai_metadata.get("follow_up_prompt_version", ""))}
          {render_crm_field("Generated", format_datetime(ai_metadata.get("summary_generated_at", "")))}
        </div>
      </section>

      <section class="detail-section" aria-labelledby="source-title">
        <h3 id="source-title">Saved JSON Output</h3>
        <p class="helper-text">Generated from the CSV report workflow for audit and CRM handoff.</p>
        <p><code>{escape(file_name)}</code></p>
        <details class="json-details">
          <summary>View saved JSON</summary>
          <pre class="json-box">{escape(json.dumps(display_result, indent=2))}</pre>
        </details>
      </section>

      <section class="detail-section" aria-labelledby="activity-title">
        <h3 id="activity-title">Activity Timeline</h3>
        <div id="activity-timeline">
          {activity_timeline}
        </div>
      </section>

      <div class="detail-footer-actions">
        <a class="secondary-link" href="/history">Back to History</a>
        <a class="detail-link" href="/lead-intake">Process Another Lead</a>
      </div>
    </section>
  </main>

  <footer>
    Built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
  <script>
    document.querySelectorAll("[data-copy-target]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const target = document.getElementById(button.dataset.copyTarget);
        if (!target) {{
          return;
        }}

        try {{
          await navigator.clipboard.writeText(target.textContent.trim());
          button.textContent = "Copied";
          await recordLeadEvent("follow_up_copied", "Follow-up draft copied", "Reviewer copied the suggested follow-up draft.");
        }} catch (error) {{
          button.textContent = "Copy failed";
        }}

        setTimeout(() => {{
          button.textContent = "Copy Draft";
        }}, 1600);
      }});
    }});

    async function recordLeadEvent(eventType, eventLabel, eventDetail) {{
      const statusWrapper = document.querySelector("[data-status-file]");
      if (!statusWrapper) {{
        return;
      }}

      await fetch(`/api/history/${{encodeURIComponent(statusWrapper.dataset.statusFile)}}/events`, {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify({{
          event_type: eventType,
          event_label: eventLabel,
          event_detail: eventDetail
        }})
      }});
    }}

    document.querySelectorAll("[data-review-status]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const wrapper = button.closest("[data-status-file]");
        const label = document.getElementById("review-status-label");
        const message = document.getElementById("review-status-message");
        if (!wrapper || !label || !message) {{
          return;
        }}

        button.disabled = true;
        message.textContent = "Updating status...";

        try {{
          const response = await fetch(`/api/history/${{encodeURIComponent(wrapper.dataset.statusFile)}}/status`, {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{review_status: button.dataset.reviewStatus}})
          }});
          const data = await response.json();

          if (!response.ok) {{
            throw new Error(data.detail || "Unable to update review status.");
          }}

          label.textContent = button.textContent;
          message.textContent = "Review status updated.";
        }} catch (error) {{
          message.textContent = error.message;
        }} finally {{
          button.disabled = false;
        }}
      }});
    }});

    document.querySelectorAll("[data-archive-lead]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const wrapper = button.closest("[data-status-file]");
        const label = document.getElementById("review-status-label");
        const message = document.getElementById("review-status-message");
        if (!wrapper || !label || !message) {{
          return;
        }}

        button.disabled = true;
        message.textContent = "Archiving lead...";

        try {{
          const response = await fetch(`/api/history/${{encodeURIComponent(wrapper.dataset.statusFile)}}/archive`, {{
            method: "POST"
          }});
          const data = await response.json();

          if (!response.ok) {{
            throw new Error(data.detail || "Unable to archive lead.");
          }}

          label.textContent = "Archived";
          message.textContent = "Lead archived. Audit history remains available.";
        }} catch (error) {{
          message.textContent = error.message;
        }} finally {{
          button.disabled = false;
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def normalize_history_filter(value: str) -> str:
    """Return a supported history classification filter."""
    normalized = (value or "all").lower()
    if normalized not in VALID_HISTORY_FILTERS:
        return "all"

    return normalized


def normalize_status_filter(value: str) -> str:
    """Return a supported review status filter."""
    normalized = (value or "all").lower()
    if normalized not in VALID_STATUS_FILTERS:
        return "all"

    return normalized


def normalize_history_sort(value: str) -> str:
    """Return a supported history sort value."""
    normalized = (value or "newest").lower()
    if normalized not in VALID_HISTORY_SORTS:
        return "newest"

    return normalized


def filter_history_rows(
    history_rows: list[dict[str, Any]],
    selected_classification: str,
    selected_status: str = "all",
    search_query: str = "",
) -> list[dict[str, Any]]:
    """Return history rows that match the selected filters."""
    normalized_search = search_query.lower().strip()
    filtered_rows = []

    for row in history_rows:
        if (
            selected_classification != "all"
            and str(row.get("classification", "")).lower() != selected_classification
        ):
            continue

        if (
            selected_status != "all"
            and str(row.get("review_status", "new")).lower() != selected_status
        ):
            continue

        if normalized_search:
            searchable_text = " ".join(
                str(row.get(field, ""))
                for field in (
                    "contact_name",
                    "company",
                    "email",
                    "service_interest",
                    "business_type",
                )
            ).lower()
            if normalized_search not in searchable_text:
                continue

        filtered_rows.append(row)

    return filtered_rows


def sort_history_rows(
    history_rows: list[dict[str, Any]],
    selected_sort: str,
) -> list[dict[str, Any]]:
    """Return rows sorted for the history table."""
    if selected_sort == "score_desc":
        return sorted(history_rows, key=get_row_score, reverse=True)

    if selected_sort == "score_asc":
        return sorted(history_rows, key=get_row_score)

    if selected_sort == "company":
        return sorted(history_rows, key=lambda row: str(row.get("company", "")).lower())

    if selected_sort == "status":
        return sorted(
            history_rows,
            key=lambda row: str(row.get("review_status", "new")).lower(),
        )

    return sorted(
        history_rows,
        key=lambda row: str(row.get("processed_at", "")),
        reverse=True,
    )


def get_row_score(row: dict[str, Any]) -> int:
    """Return a numeric score for sorting."""
    try:
        return int(row.get("lead_score", 0))
    except (TypeError, ValueError):
        return 0


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


def get_status_counts(history_rows: list[dict[str, Any]]) -> dict[str, int]:
    """Return counts for review status filters."""
    counts = {status: 0 for status in VALID_STATUS_FILTERS}
    counts["all"] = len(history_rows)

    for row in history_rows:
        review_status = str(row.get("review_status", "new")).lower()
        if review_status in counts:
            counts[review_status] += 1

    return counts


def get_history_analytics(history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return top-level lead history analytics."""
    scores = [get_row_score(row) for row in history_rows if row.get("lead_score") != ""]
    average_score = round(sum(scores) / len(scores)) if scores else 0

    return {
        "total": len(history_rows),
        "hot": sum(
            1
            for row in history_rows
            if str(row.get("classification", "")).lower() == "hot"
        ),
        "average_score": f"{average_score}/100",
        "new": sum(
            1
            for row in history_rows
            if str(row.get("review_status", "new")).lower() == "new"
        ),
    }


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
            <a class="history-filter-link {active_class}" href="{build_history_url(classification=value, page=1)}"{aria_current}>
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


def render_history_controls(
    selected_classification: str,
    selected_status: str,
    selected_sort: str,
    search_query: str,
    status_counts: dict[str, int],
) -> str:
    """Return search, status, and sort controls for the history page."""
    status_options = render_select_options(
        options={
            "all": f"All statuses ({status_counts.get('all', 0)})",
            "new": f"New ({status_counts.get('new', 0)})",
            "reviewed": f"Reviewed ({status_counts.get('reviewed', 0)})",
            "contacted": f"Contacted ({status_counts.get('contacted', 0)})",
            "needs_follow_up": f"Needs follow-up ({status_counts.get('needs_follow_up', 0)})",
            "archived": f"Archived ({status_counts.get('archived', 0)})",
        },
        selected_value=selected_status,
    )
    sort_options = render_select_options(
        options={
            "newest": "Newest first",
            "score_desc": "Highest score",
            "score_asc": "Lowest score",
            "company": "Company A-Z",
            "status": "Review status",
        },
        selected_value=selected_sort,
    )

    return f"""
      <form class="history-controls" method="get" action="/history">
        <input type="hidden" name="classification" value="{escape(selected_classification)}">
        <label>
          Search
          <input name="search" value="{escape(search_query)}" placeholder="Name, company, email, or service">
        </label>
        <label>
          Review Status
          <select name="status">
            {status_options}
          </select>
        </label>
        <label>
          Sort
          <select name="sort">
            {sort_options}
          </select>
        </label>
        <button class="secondary" type="submit">Apply</button>
        <a class="secondary-link compact" href="/history">Reset</a>
      </form>
    """


def render_bulk_actions() -> str:
    """Return bulk status controls for the history table."""
    return """
      <div class="bulk-actions" aria-label="Bulk lead actions">
        <div>
          <p class="toolbar-label">Bulk Actions</p>
          <p class="helper-text" data-bulk-message>Select leads, then update their review status or archive them.</p>
        </div>
        <div class="bulk-action-controls">
          <select data-bulk-status aria-label="Bulk review status">
            <option value="reviewed">Reviewed</option>
            <option value="contacted">Contacted</option>
            <option value="needs_follow_up">Needs follow-up</option>
          </select>
          <button class="secondary" type="button" data-bulk-action="status">Update Selected</button>
          <button class="secondary danger" type="button" data-bulk-action="archive">Archive Selected</button>
        </div>
      </div>
    """


def render_select_options(options: dict[str, str], selected_value: str) -> str:
    """Return HTML select options."""
    rendered_options = []
    for value, label in options.items():
        selected = " selected" if value == selected_value else ""
        rendered_options.append(
            f'<option value="{escape(value)}"{selected}>{escape(label)}</option>'
        )

    return "\n".join(rendered_options)


def render_pagination(
    selected_classification: str,
    selected_status: str,
    selected_sort: str,
    search_query: str,
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
            <a class="history-page-link {active_class}" href="{build_history_url(selected_classification, page_number, selected_status, selected_sort, search_query)}"{aria_current}>
              {page_number}
            </a>
            """
        )

    return f"""
      <nav class="pagination" aria-label="History pagination">
        <span class="pagination-summary">Page {current_page} of {total_pages}</span>
        <div class="pagination-controls">
          <a class="history-page-link pagination-step {previous_class}" href="{build_history_url(selected_classification, previous_page, selected_status, selected_sort, search_query)}">Previous</a>
          {"".join(page_links)}
          <a class="history-page-link pagination-step {next_class}" href="{build_history_url(selected_classification, next_page, selected_status, selected_sort, search_query)}">Next</a>
        </div>
      </nav>
    """


def build_history_url(
    classification: str,
    page: int,
    status: str = "all",
    sort: str = "newest",
    search: str = "",
) -> str:
    """Build a history page URL for filters and pagination."""
    params = []

    if classification != "all":
        params.append(("classification", classification))
    if status != "all":
        params.append(("status", status))
    if sort != "newest":
        params.append(("sort", sort))
    if search:
        params.append(("search", search))

    params.append(("page", str(page)))
    query = "&".join(f"{key}={quote(value)}" for key, value in params)

    return f"/history?{query}"


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
    processed_at = format_datetime(row.get("processed_at", ""))
    review_status = str(row.get("review_status", "new")).lower()
    review_status_label = format_display_label(review_status)

    return f"""
            <tr>
              <td><input type="checkbox" data-lead-checkbox value="{escape(file_name)}" aria-label="Select {escape(str(row.get("contact_name", "lead")))}"></td>
              <td><a class="row-link" href="{escape(detail_url)}">{escape(str(row.get("contact_name", "")))}</a></td>
              <td>{escape(str(row.get("company", "")))}</td>
              <td><span class="badge {classification}">{escape(classification)}</span></td>
              <td>{escape(score)}</td>
              <td>{escape(str(row.get("lead_rating", "")))}</td>
              <td><span class="status-pill {escape(review_status)}" data-row-status>{escape(review_status_label)}</span></td>
              <td>{escape(processed_at)}</td>
              <td><a class="table-action-link" href="{escape(detail_url)}">View Details</a></td>
            </tr>
    """


def normalize_detail_classification(classification: Any) -> str:
    """Return a valid CSS class for one lead classification."""
    normalized = str(classification).lower()
    if normalized in {"hot", "warm", "cold"}:
        return normalized

    return "cold"


def render_crm_field(label: str, value: Any, fallback: str = "Not available") -> str:
    """Return one CRM-ready field block."""
    display_value = str(value or "").strip() or fallback

    return f"""
          <div>
            <span>{escape(label)}</span>
            {escape(display_value)}
          </div>
    """


def render_activity_timeline(events: list[dict[str, Any]]) -> str:
    """Return the saved lead activity timeline."""
    if not events:
        return '<p class="helper-text">No activity recorded yet.</p>'

    grouped_events = group_activity_events(events)
    event_items = []
    for event in grouped_events[:6]:
        count = event.get("count", 1)
        count_label = (
            f' <span class="activity-count">x{escape(str(count))}</span>'
            if count > 1
            else ""
        )
        event_items.append(
            f"""
            <li>
              <span>{escape(format_datetime(event.get("created_at", "")))}</span>
              <strong>{escape(str(event.get("event_label", "")))}{count_label}</strong>
              <p>{escape(str(event.get("event_detail", "")))}</p>
            </li>
            """
        )

    overflow_note = ""
    if len(grouped_events) > 6:
        overflow_note = '<p class="helper-text activity-summary-note">Showing latest 6 activity groups.</p>'

    return f"""
          <ol class="activity-list">
            {"".join(event_items)}
          </ol>
          {overflow_note}
    """


def group_activity_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group repeated timeline entries while preserving newest-first ordering."""
    grouped_events: list[dict[str, Any]] = []
    grouped_index: dict[tuple[str, str], dict[str, Any]] = {}

    for event in events:
        label = str(event.get("event_label", "")).strip()
        detail = str(event.get("event_detail", "")).strip()
        key = (label, detail)

        if key in grouped_index:
            grouped_index[key]["count"] += 1
            continue

        grouped_event = dict(event)
        grouped_event["count"] = 1
        grouped_events.append(grouped_event)
        grouped_index[key] = grouped_event

    return grouped_events


def get_ai_metadata(result: dict[str, Any]) -> dict[str, Any]:
    """Return AI metadata from current or legacy saved output shapes."""
    crm_ready = result.get("crm_ready", {})
    ai_outputs = result.get("ai_outputs", {})
    metadata = result.get("metadata", {})

    if isinstance(crm_ready.get("ai_metadata"), dict):
        return crm_ready["ai_metadata"]

    if isinstance(ai_outputs.get("metadata"), dict):
        return ai_outputs["metadata"]

    if isinstance(metadata.get("ai"), dict):
        return metadata["ai"]

    return {}


def format_display_label(value: Any) -> str:
    """Convert stored enum-style values into readable labels."""
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    return raw_value.replace("_", " ").title()


def format_datetime(value: Any) -> str:
    """Convert an ISO timestamp into a concise readable UTC timestamp."""
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    try:
        parsed_datetime = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return raw_value

    return (
        f"{parsed_datetime.strftime('%B')} {parsed_datetime.day}, "
        f"{parsed_datetime.year}, "
        f"{parsed_datetime.strftime('%I').lstrip('0')}:{parsed_datetime.strftime('%M %p')} UTC"
    )


def format_score(lead_score: Any, max_score: Any) -> str:
    """Format score values for the history table."""
    if lead_score == "" and max_score == "":
        return ""

    return f"{lead_score}/{max_score}"
