"""Operational readiness checks and status page rendering."""

import sqlite3
import tempfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from app.automation.storage import get_database_path, initialize_database, list_saved_outputs
from app.config import APP_ENV, OPENAI_MODEL, WORKFLOW_VERSION


def build_operations_status(output_dir: str | Path = "data/outputs") -> dict[str, Any]:
    """Return deployment and storage readiness details."""
    output_path = Path(output_dir)
    output_check = check_output_directory(output_path)
    database_check = check_sqlite_database(output_path)
    history_rows = list_saved_outputs(output_dir=output_path) if output_check["ok"] else []
    latest_event = get_latest_event(output_path) if database_check["ok"] else None

    checks = {
        "output_directory": output_check,
        "sqlite_database": database_check,
        "openai_model": {
            "ok": bool(OPENAI_MODEL),
            "status": "ok" if OPENAI_MODEL else "missing",
            "detail": OPENAI_MODEL or "No model configured.",
        },
        "workflow_version": {
            "ok": bool(WORKFLOW_VERSION),
            "status": "ok" if WORKFLOW_VERSION else "missing",
            "detail": WORKFLOW_VERSION or "No workflow version configured.",
        },
    }
    overall_ok = all(check["ok"] for check in checks.values())

    return {
        "status": "ok" if overall_ok else "degraded",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": APP_ENV,
        "model": OPENAI_MODEL,
        "workflow_version": WORKFLOW_VERSION,
        "storage": {
            "output_directory": str(output_path),
            "database_path": str(get_database_path(output_path)),
        },
        "counts": {
            "saved_leads": len(history_rows),
            "new_reviews": count_rows_by_value(history_rows, "review_status", "new"),
            "hot_leads": count_rows_by_value(history_rows, "classification", "hot"),
        },
        "latest_processed_lead": history_rows[0] if history_rows else None,
        "latest_audit_event": latest_event,
        "checks": checks,
    }


def check_output_directory(output_path: Path) -> dict[str, Any]:
    """Confirm output storage exists and can be written."""
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output_path,
            prefix=".health-",
            suffix=".tmp",
            delete=True,
        ) as file:
            file.write(b"ok")

        return {
            "ok": True,
            "status": "ok",
            "detail": f"Writable output directory: {output_path}",
        }
    except OSError as error:
        return {
            "ok": False,
            "status": "error",
            "detail": f"Output directory is not writable: {error}",
        }


def check_sqlite_database(output_path: Path) -> dict[str, Any]:
    """Confirm SQLite can initialize and answer a simple query."""
    try:
        database_path = initialize_database(output_path)
        with sqlite3.connect(database_path) as connection:
            connection.execute("SELECT 1").fetchone()

        return {
            "ok": True,
            "status": "ok",
            "detail": f"SQLite reachable: {database_path}",
        }
    except sqlite3.Error as error:
        return {
            "ok": False,
            "status": "error",
            "detail": f"SQLite check failed: {error}",
        }


def get_latest_event(output_path: Path) -> dict[str, Any] | None:
    """Return the latest audit event across all saved leads."""
    database_path = initialize_database(output_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                id,
                file_name,
                event_type,
                event_label,
                event_detail,
                created_at
            FROM lead_events
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    return dict(row) if row else None


def count_rows_by_value(rows: list[dict[str, Any]], key: str, value: str) -> int:
    """Count compact history rows by a normalized field value."""
    return sum(1 for row in rows if str(row.get(key, "")).lower() == value)


def render_system_status_page(status: dict[str, Any]) -> str:
    """Return the browser-facing operations status page."""
    latest_lead = status.get("latest_processed_lead") or {}
    latest_event = status.get("latest_audit_event") or {}
    status_label = status.get("status", "unknown")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>System Status</title>
  <link rel="stylesheet" href="/static/lead-intake.css">
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>System Status</h1>
        <p class="subtitle">Operational readiness snapshot for lead intake, storage, AI configuration, and review workflows.</p>
      </div>
      <nav class="header-actions" aria-label="System status navigation">
        <a class="nav-link" href="/history">Review History</a>
        <a class="nav-link" href="/lead-intake">Process Lead</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="value-strip" aria-label="System summary">
      <div class="value-item">
        <span>Overall Status</span>
        <strong>{escape(status_label.upper())}</strong>
        <p>Combined result from storage, database, model, and workflow checks.</p>
      </div>
      <div class="value-item">
        <span>Saved Leads</span>
        <strong>{escape(str(status["counts"]["saved_leads"]))}</strong>
        <p>Lead records indexed for review and handoff.</p>
      </div>
      <div class="value-item">
        <span>New Reviews</span>
        <strong>{escape(str(status["counts"]["new_reviews"]))}</strong>
        <p>Leads still waiting for a human review status.</p>
      </div>
      <div class="value-item">
        <span>Hot Leads</span>
        <strong>{escape(str(status["counts"]["hot_leads"]))}</strong>
        <p>Highest-priority opportunities in saved history.</p>
      </div>
    </section>

    <section class="panel detail-panel" aria-labelledby="ops-title">
      <div class="detail-header">
        <div>
          <p class="detail-eyebrow">Operations Readiness</p>
          <h2 id="ops-title">Runtime and Storage Checks</h2>
          <p class="helper-text">Last checked: {escape(status.get("checked_at", ""))}</p>
        </div>
        <span class="status-pill {escape(status_label)}">{escape(status_label)}</span>
      </div>

      <section class="detail-section" aria-labelledby="checks-title">
        <h3 id="checks-title">System Checks</h3>
        <div class="crm-grid">
          {render_status_field("Output Directory", status["checks"]["output_directory"])}
          {render_status_field("SQLite Database", status["checks"]["sqlite_database"])}
          {render_status_field("OpenAI Model", status["checks"]["openai_model"])}
          {render_status_field("Workflow Version", status["checks"]["workflow_version"])}
        </div>
      </section>

      <section class="detail-section" aria-labelledby="config-title">
        <h3 id="config-title">Configuration</h3>
        <div class="crm-grid">
          {render_field("Environment", status.get("environment", ""))}
          {render_field("Model", status.get("model", ""))}
          {render_field("Workflow Version", status.get("workflow_version", ""))}
          {render_field("Output Directory", status["storage"]["output_directory"])}
          {render_field("Database Path", status["storage"]["database_path"])}
        </div>
      </section>

      <section class="detail-section" aria-labelledby="latest-title">
        <h3 id="latest-title">Latest Activity</h3>
        <div class="crm-grid">
          {render_field("Latest Lead", latest_lead.get("contact_name", "No saved leads yet"))}
          {render_field("Latest Lead File", latest_lead.get("file_name", ""))}
          {render_field("Latest Audit Event", latest_event.get("event_label", "No audit events yet"))}
          {render_field("Audit Event Time", latest_event.get("created_at", ""))}
        </div>
      </section>

      <section
        class="detail-section integration-dashboard"
        aria-labelledby="integration-status-title"
        data-integration-dashboard
      >
        <div class="detail-header">
          <div>
            <h3 id="integration-status-title">Integration Status</h3>
            <p class="helper-text">Downstream delivery health from Google Sheets, Airtable, and HubSpot.</p>
          </div>
          <span class="status-pill" id="integration-dashboard-message">Loading</span>
        </div>

        <div
          class="crm-grid"
          id="integration-provider-summary"
          aria-live="polite"
          data-empty-text="Integration status is loading."
        >
          <div>
            <span>Status</span>
            <strong>Loading</strong>
            <p class="helper-text">Checking integration providers.</p>
          </div>
        </div>
      </section>

      <section
        class="detail-section integration-dashboard"
        aria-labelledby="failed-runs-title"
        data-integration-failed-runs
      >
        <div class="detail-header">
          <div>
            <h3 id="failed-runs-title">Recent Failed Integration Runs</h3>
            <p class="helper-text">Retry failed downstream deliveries after checking provider configuration.</p>
          </div>
        </div>

        <div id="integration-retry-feedback" class="helper-text" role="status" aria-live="polite"></div>
        <div id="failed-integration-runs" aria-live="polite">
          <p class="helper-text">Loading failed integration runs.</p>
        </div>
      </section>
    </section>
  </main>

  <footer>
    Built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>
  <script>
    const providerLabels = {{
      google_sheets: "Google Sheets",
      airtable: "Airtable",
      hubspot: "HubSpot",
    }};

    function escapeHtml(value) {{
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function formatStatus(value) {{
      return String(value || "unknown").replace(/_/g, " ");
    }}

    async function loadIntegrationStatus() {{
      const summary = document.getElementById("integration-provider-summary");
      const message = document.getElementById("integration-dashboard-message");

      try {{
        const response = await fetch("/api/integrations/status");
        if (!response.ok) {{
          throw new Error("Status request failed.");
        }}
        const data = await response.json();
        const providers = data.providers || {{}};
        summary.innerHTML = Object.entries(providerLabels).map(([key, label]) => {{
          const provider = providers[key] || {{}};
          const enabled = provider.enabled ? "Enabled" : "Disabled";
          return `
            <div>
              <span>${{escapeHtml(label)}}</span>
              <strong>${{escapeHtml(enabled)}}</strong>
              <p class="helper-text">
                Last: ${{escapeHtml(formatStatus(provider.last_status))}}<br>
                Success: ${{escapeHtml(provider.success_count || 0)}} |
                Failed: ${{escapeHtml(provider.failed_count || 0)}}
              </p>
            </div>
          `;
        }}).join("");
        message.textContent = data.failed_total ? `${{data.failed_total}} failed` : "Healthy";
      }} catch (error) {{
        summary.innerHTML = '<p class="helper-text">Integration status could not be loaded.</p>';
        message.textContent = "Unavailable";
      }}
    }}

    async function loadFailedIntegrationRuns() {{
      const container = document.getElementById("failed-integration-runs");

      try {{
        const response = await fetch("/api/integrations/runs?status=failed");
        if (!response.ok) {{
          throw new Error("Failed runs request failed.");
        }}
        const data = await response.json();
        const runs = data.runs || [];

        if (!runs.length) {{
          container.innerHTML = '<p class="helper-text">No failed integration runs.</p>';
          return;
        }}

        container.innerHTML = `
          <div class="table-wrap">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Provider</th>
                  <th>Lead/File</th>
                  <th>Message</th>
                  <th>Retry Count</th>
                  <th>Created At</th>
                  <th>Last Retry At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${{runs.map((run) => `
                  <tr>
                    <td>${{escapeHtml(run.id)}}</td>
                    <td>${{escapeHtml(providerLabels[run.provider] || run.provider)}}</td>
                    <td>${{renderLeadFileCell(run)}}</td>
                    <td>${{escapeHtml(run.message || "Delivery failed.")}}</td>
                    <td>${{escapeHtml(run.retry_count || 0)}}</td>
                    <td>${{escapeHtml(run.created_at || "")}}</td>
                    <td>${{escapeHtml(run.last_retry_at || "")}}</td>
                    <td>
                      <button type="button" class="copy-button" data-retry-run-id="${{escapeHtml(run.id)}}">Retry</button>
                    </td>
                  </tr>
                `).join("")}}
              </tbody>
            </table>
          </div>
        `;
      }} catch (error) {{
        container.innerHTML = '<p class="helper-text">Failed integration runs could not be loaded.</p>';
      }}
    }}

    function renderLeadFileCell(run) {{
      const fileName = run.file_name || "";
      if (!fileName) {{
        return escapeHtml(run.lead_id || "");
      }}
      return `<a href="/history/${{encodeURIComponent(fileName)}}">${{escapeHtml(fileName)}}</a>`;
    }}

    async function retryIntegrationRun(runId, button) {{
      const feedback = document.getElementById("integration-retry-feedback");
      button.disabled = true;
      feedback.textContent = `Retrying integration run ${{runId}}...`;

      try {{
        const response = await fetch(`/api/integrations/retry/${{encodeURIComponent(runId)}}`, {{
          method: "POST",
        }});
        const data = await response.json();

        if (!response.ok) {{
          throw new Error(data.detail || "Retry failed.");
        }}

        feedback.textContent = `Retry ${{data.status}} for ${{providerLabels[data.provider] || data.provider}} run ${{data.run_id}}.`;
      }} catch (error) {{
        feedback.textContent = error.message || "Retry failed.";
      }} finally {{
        await loadIntegrationStatus();
        await loadFailedIntegrationRuns();
      }}
    }}

    document.addEventListener("click", (event) => {{
      const button = event.target.closest("[data-retry-run-id]");
      if (!button) {{
        return;
      }}
      retryIntegrationRun(button.dataset.retryRunId, button);
    }});

    document.addEventListener("DOMContentLoaded", () => {{
      loadIntegrationStatus();
      loadFailedIntegrationRuns();
    }});
  </script>
</body>
</html>
"""


def render_status_field(label: str, check: dict[str, Any]) -> str:
    """Return one status check field."""
    status = check.get("status", "unknown")
    detail = check.get("detail", "")
    return f"""
          <div>
            <span>{escape(label)}</span>
            <strong>{escape(str(status).upper())}</strong>
            <p class="helper-text">{escape(str(detail))}</p>
          </div>
    """


def render_field(label: str, value: Any) -> str:
    """Return one operations detail field."""
    return f"""
          <div>
            <span>{escape(label)}</span>
            {escape(str(value or ""))}
          </div>
    """
