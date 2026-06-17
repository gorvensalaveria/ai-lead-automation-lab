"""Save automation outputs locally."""

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from io import StringIO
from typing import Any

from app.config import (
    CLASSIFICATION_PROMPT_VERSION,
    FOLLOW_UP_PROMPT_VERSION,
    OPENAI_MODEL,
    SUMMARY_PROMPT_VERSION,
    WORKFLOW_VERSION,
)


HISTORY_CSV_COLUMNS = [
    "processed_at",
    "lead_id",
    "contact_name",
    "company",
    "email",
    "business_type",
    "service_interest",
    "classification",
    "lead_score",
    "max_score",
    "lead_rating",
    "review_status",
    "recommended_next_action",
    "file_name",
    "output_path",
]

VALID_REVIEW_STATUSES = {
    "new",
    "reviewed",
    "contacted",
    "archived",
    "needs_follow_up",
}

VALID_EVENT_TYPES = {
    "lead_processed",
    "lead_viewed",
    "csv_exported",
    "google_sheets_exported",
    "review_status_changed",
    "follow_up_copied",
    "lead_archived",
}

VALID_INTEGRATION_RUN_STATUSES = {
    "disabled",
    "success",
    "failed",
    "skipped",
    "retrying",
}

INTEGRATION_RUN_PUBLIC_FIELDS = [
    "id",
    "file_name",
    "lead_id",
    "provider",
    "status",
    "external_id",
    "message",
    "retry_count",
    "last_retry_at",
    "created_at",
    "updated_at",
]


def save_output(result: dict[str, Any], output_dir: str | Path = "data/outputs") -> Path:
    """Save one automation result as JSON and index it in SQLite."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    lead_id = result["lead"]["lead_id"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = output_path / f"{lead_id}_{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    save_result_to_database(result=result, file_path=file_path, output_dir=output_path)

    return file_path


def list_saved_outputs(output_dir: str | Path = "data/outputs") -> list[dict[str, Any]]:
    """Return saved automation outputs as compact history rows."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return []

    sync_json_outputs_to_database(output_dir=output_path)
    database_rows = list_database_history_rows(output_dir=output_path)
    if database_rows:
        return database_rows

    history_rows = []
    for file_path in output_path.glob("*.json"):
        try:
            result = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        history_rows.append(build_history_row(result=result, file_path=file_path))

    return sorted(
        history_rows,
        key=lambda row: row["processed_at"],
        reverse=True,
    )


def load_saved_output(
    file_name: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any]:
    """Load one saved automation output by file name."""
    output_path = Path(output_dir)
    file_path = get_safe_output_file_path(file_name=file_name, output_path=output_path)
    database_result = load_saved_output_from_database(file_name, output_dir=output_path)

    if database_result is not None:
        return database_result

    if not file_path.exists():
        raise FileNotFoundError(f"Saved output not found: {file_name}")

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Saved output is not valid JSON: {file_name}") from error


def get_safe_output_file_path(file_name: str, output_path: Path) -> Path:
    """Return a safe JSON output path without allowing path traversal."""
    requested_path = Path(file_name)

    if requested_path.name != file_name or requested_path.suffix != ".json":
        raise ValueError("Saved output file name must be a JSON file name only.")

    return output_path / requested_path.name


def get_database_path(output_dir: str | Path = "data/outputs") -> Path:
    """Return the SQLite database path for saved lead metadata."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path / "lead_intake.db"


def initialize_database(output_dir: str | Path = "data/outputs") -> Path:
    """Create the saved lead SQLite database if needed."""
    database_path = get_database_path(output_dir)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_leads (
                file_name TEXT PRIMARY KEY,
                output_path TEXT NOT NULL,
                processed_at TEXT,
                lead_id TEXT,
                contact_name TEXT,
                company TEXT,
                email TEXT,
                business_type TEXT,
                service_interest TEXT,
                classification TEXT,
                lead_score INTEGER,
                max_score INTEGER,
                lead_rating TEXT,
                review_status TEXT NOT NULL DEFAULT 'new',
                recommended_next_action TEXT,
                result_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_saved_leads_processed_at ON saved_leads(processed_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_saved_leads_classification ON saved_leads(classification)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_saved_leads_review_status ON saved_leads(review_status)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_label TEXT NOT NULL,
                event_detail TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(file_name) REFERENCES saved_leads(file_name)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_lead_events_file_name ON lead_events(file_name)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_lead_events_created_at ON lead_events(created_at)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT UNIQUE NOT NULL,
                lead_id TEXT,
                file_name TEXT,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS integration_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                lead_id TEXT,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                external_id TEXT,
                message TEXT,
                response_json TEXT,
                retry_count INTEGER DEFAULT 0,
                last_retry_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_integration_runs_file_name ON integration_runs(file_name)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_integration_runs_lead_id ON integration_runs(lead_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_integration_runs_provider ON integration_runs(provider)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_integration_runs_status ON integration_runs(status)"
        )

    return database_path


def create_integration_run(
    *,
    file_name: str,
    lead_id: str | None,
    provider: str,
    status: str,
    external_id: str | None = None,
    message: str | None = None,
    response_json: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> int:
    """Create one downstream integration run record."""
    output_path = Path(output_dir or "data/outputs")
    safe_file_name = get_safe_output_file_path(
        file_name=file_name,
        output_path=output_path,
    ).name
    normalized_status = normalize_integration_run_status(status)
    normalized_provider = normalize_integration_provider(provider)
    now = datetime.now(timezone.utc).isoformat()
    initialize_database(output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO integration_runs (
                file_name,
                lead_id,
                provider,
                status,
                external_id,
                message,
                response_json,
                retry_count,
                last_retry_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
            """,
            (
                safe_file_name,
                lead_id,
                normalized_provider,
                normalized_status,
                external_id,
                message,
                json.dumps(response_json) if response_json is not None else None,
                now,
                now,
            ),
        )

    return int(cursor.lastrowid)


def list_integration_runs(
    *,
    file_name: str | None = None,
    lead_id: str | None = None,
    provider: str | None = None,
    status: str | None = None,
    output_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return safe integration run rows, optionally filtered."""
    output_path = Path(output_dir or "data/outputs")
    initialize_database(output_path)

    clauses = []
    values: list[Any] = []

    if file_name:
        clauses.append("file_name = ?")
        values.append(get_safe_output_file_path(file_name=file_name, output_path=output_path).name)
    if lead_id:
        clauses.append("lead_id = ?")
        values.append(str(lead_id))
    if provider:
        clauses.append("provider = ?")
        values.append(normalize_integration_provider(provider))
    if status:
        clauses.append("status = ?")
        values.append(normalize_integration_run_status(status))

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    select_fields = ", ".join(INTEGRATION_RUN_PUBLIC_FIELDS)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            SELECT {select_fields}
            FROM integration_runs
            {where_sql}
            ORDER BY created_at DESC, id DESC
            """,
            values,
        ).fetchall()

    return [dict(row) for row in rows]


def get_integration_run(
    run_id: int,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return one integration run, including internal retry metadata."""
    output_path = Path(output_dir or "data/outputs")
    initialize_database(output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                id,
                file_name,
                lead_id,
                provider,
                status,
                external_id,
                message,
                response_json,
                retry_count,
                last_retry_at,
                created_at,
                updated_at
            FROM integration_runs
            WHERE id = ?
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    if result.get("response_json"):
        result["response_json"] = json.loads(result["response_json"])
    else:
        result["response_json"] = None
    return result


def update_integration_run_after_retry(
    *,
    run_id: int,
    status: str,
    external_id: str | None = None,
    message: str | None = None,
    response_json: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> None:
    """Update one existing integration run after a manual retry attempt."""
    output_path = Path(output_dir or "data/outputs")
    normalized_status = normalize_integration_run_status(status)
    now = datetime.now(timezone.utc).isoformat()
    initialize_database(output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE integration_runs
            SET
                status = ?,
                external_id = ?,
                message = ?,
                response_json = ?,
                retry_count = retry_count + 1,
                last_retry_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                normalized_status,
                external_id,
                message,
                json.dumps(response_json) if response_json is not None else None,
                now,
                now,
                run_id,
            ),
        )

    if cursor.rowcount == 0:
        raise FileNotFoundError(f"Integration run not found: {run_id}")


def get_integration_status_summary(
    *,
    output_dir: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Return aggregate status counts by integration provider."""
    output_path = Path(output_dir or "data/outputs")
    initialize_database(output_path)
    providers = ["google_sheets", "airtable", "hubspot"]
    summary: dict[str, dict[str, Any]] = {
        provider: {
            "last_status": None,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }
        for provider in providers
    }

    with sqlite3.connect(get_database_path(output_path)) as connection:
        count_rows = connection.execute(
            """
            SELECT provider, status, COUNT(*) AS count
            FROM integration_runs
            GROUP BY provider, status
            """
        ).fetchall()
        latest_rows = connection.execute(
            """
            SELECT provider, status
            FROM integration_runs
            WHERE id IN (
                SELECT MAX(id)
                FROM integration_runs
                GROUP BY provider
            )
            """
        ).fetchall()

    for provider, status, count in count_rows:
        provider_summary = summary.setdefault(
            provider,
            {
                "last_status": None,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            },
        )
        if status == "success":
            provider_summary["success_count"] = count
        elif status == "failed":
            provider_summary["failed_count"] = count
        elif status == "skipped":
            provider_summary["skipped_count"] = count

    for provider, status in latest_rows:
        summary.setdefault(
            provider,
            {
                "last_status": None,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            },
        )["last_status"] = status

    return summary


def load_idempotency_response(
    idempotency_key: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any] | None:
    """Return a saved webhook response for an idempotency key."""
    normalized_key = str(idempotency_key or "").strip()
    if not normalized_key:
        return None

    output_path = Path(output_dir)
    initialize_database(output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            """
            SELECT response_json
            FROM idempotency_keys
            WHERE idempotency_key = ?
            LIMIT 1
            """,
            (normalized_key,),
        ).fetchone()

    if not row:
        return None

    return json.loads(row[0])


def save_idempotency_response(
    idempotency_key: str,
    response_payload: dict[str, Any],
    lead_id: str = "",
    file_name: str = "",
    output_dir: str | Path = "data/outputs",
) -> None:
    """Save a successful webhook response for future duplicate requests."""
    normalized_key = str(idempotency_key or "").strip()
    if not normalized_key:
        return

    output_path = Path(output_dir)
    initialize_database(output_path)
    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(get_database_path(output_path)) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO idempotency_keys (
                idempotency_key,
                lead_id,
                file_name,
                response_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                normalized_key,
                str(lead_id or ""),
                str(file_name or ""),
                json.dumps(response_payload),
                created_at,
            ),
        )


def save_result_to_database(
    result: dict[str, Any],
    file_path: Path,
    output_dir: str | Path = "data/outputs",
    review_status: str = "new",
) -> None:
    """Save or update one result in the SQLite history database."""
    initialize_database(output_dir)
    row = build_history_row(result=result, file_path=file_path)
    normalized_status = normalize_review_status(review_status)

    with sqlite3.connect(get_database_path(output_dir)) as connection:
        connection.execute(
            """
            INSERT INTO saved_leads (
                file_name,
                output_path,
                processed_at,
                lead_id,
                contact_name,
                company,
                email,
                business_type,
                service_interest,
                classification,
                lead_score,
                max_score,
                lead_rating,
                review_status,
                recommended_next_action,
                result_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_name) DO UPDATE SET
                output_path = excluded.output_path,
                processed_at = excluded.processed_at,
                lead_id = excluded.lead_id,
                contact_name = excluded.contact_name,
                company = excluded.company,
                email = excluded.email,
                business_type = excluded.business_type,
                service_interest = excluded.service_interest,
                classification = excluded.classification,
                lead_score = excluded.lead_score,
                max_score = excluded.max_score,
                lead_rating = excluded.lead_rating,
                recommended_next_action = excluded.recommended_next_action,
                result_json = excluded.result_json
            """,
            (
                row["file_name"],
                row["output_path"],
                row["processed_at"],
                row["lead_id"],
                row["contact_name"],
                row["company"],
                row["email"],
                row["business_type"],
                row["service_interest"],
                row["classification"],
                row["lead_score"],
                row["max_score"],
                row["lead_rating"],
                normalized_status,
                row["recommended_next_action"],
                json.dumps(result),
            ),
        )

    record_lead_event(
        file_name=row["file_name"],
        event_type="lead_processed",
        event_label="Lead processed",
        event_detail="AI qualification result saved and indexed.",
        output_dir=output_dir,
        dedupe=True,
    )


def sync_json_outputs_to_database(output_dir: str | Path = "data/outputs") -> None:
    """Import JSON output files into SQLite without changing existing statuses."""
    output_path = Path(output_dir)
    initialize_database(output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        existing_files = {
            row[0]
            for row in connection.execute("SELECT file_name FROM saved_leads").fetchall()
        }

    for file_path in output_path.glob("*.json"):
        if file_path.name in existing_files:
            continue

        try:
            result = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        save_result_to_database(result=result, file_path=file_path, output_dir=output_path)


def list_database_history_rows(output_dir: str | Path = "data/outputs") -> list[dict[str, Any]]:
    """Return history rows from SQLite."""
    initialize_database(output_dir)

    with sqlite3.connect(get_database_path(output_dir)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                file_name,
                output_path,
                processed_at,
                lead_id,
                contact_name,
                company,
                email,
                business_type,
                service_interest,
                classification,
                lead_score,
                max_score,
                lead_rating,
                review_status,
                recommended_next_action
            FROM saved_leads
            ORDER BY processed_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_review_status(
    file_name: str,
    review_status: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any]:
    """Update a saved lead review status and return its history row."""
    output_path = Path(output_dir)
    get_safe_output_file_path(file_name=file_name, output_path=output_path)
    normalized_status = normalize_review_status(review_status)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            "SELECT result_json, output_path FROM saved_leads WHERE file_name = ?",
            (file_name,),
        ).fetchone()

        if not row:
            raise FileNotFoundError(f"Saved output not found: {file_name}")

        result = json.loads(row[0])
        result["review_status"] = normalized_status
        result.setdefault("crm_ready", {})["review_status"] = normalized_status

        cursor = connection.execute(
            """
            UPDATE saved_leads
            SET review_status = ?, result_json = ?
            WHERE file_name = ?
            """,
            (normalized_status, json.dumps(result), file_name),
        )

        if cursor.rowcount == 0:
            raise FileNotFoundError(f"Saved output not found: {file_name}")

    file_path = output_path / file_name
    if file_path.exists():
        file_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    record_lead_event(
        file_name=file_name,
        event_type="review_status_changed",
        event_label="Review status changed",
        event_detail=f"Status set to {normalized_status.replace('_', ' ')}.",
        output_dir=output_path,
    )

    for row in list_database_history_rows(output_dir=output_path):
        if row["file_name"] == file_name:
            return row

    raise FileNotFoundError(f"Saved output not found: {file_name}")


def archive_saved_output(
    file_name: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any]:
    """Archive a saved lead without deleting its audit record."""
    row = update_review_status(
        file_name=file_name,
        review_status="archived",
        output_dir=output_dir,
    )
    record_lead_event(
        file_name=file_name,
        event_type="lead_archived",
        event_label="Lead archived",
        event_detail="Lead hidden from active follow-up queues while audit history remains available.",
        output_dir=output_dir,
    )

    return row


def bulk_update_review_status(
    file_names: list[str],
    review_status: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any]:
    """Update several saved lead statuses and return per-file results."""
    normalized_status = normalize_review_status(review_status)
    if not file_names:
        raise ValueError("At least one saved output file name is required.")

    updated_rows = []
    errors = []

    for file_name in file_names:
        try:
            if normalized_status == "archived":
                updated_rows.append(
                    archive_saved_output(file_name=file_name, output_dir=output_dir)
                )
            else:
                updated_rows.append(
                    update_review_status(
                        file_name=file_name,
                        review_status=normalized_status,
                        output_dir=output_dir,
                    )
                )
        except (ValueError, FileNotFoundError) as error:
            errors.append({"file_name": file_name, "error": str(error)})

    return {
        "requested": len(file_names),
        "updated": updated_rows,
        "errors": errors,
    }


def record_lead_event(
    file_name: str,
    event_type: str,
    event_label: str,
    event_detail: str = "",
    output_dir: str | Path = "data/outputs",
    dedupe: bool = False,
) -> dict[str, Any]:
    """Record one audit event for a saved lead."""
    output_path = Path(output_dir)
    get_safe_output_file_path(file_name=file_name, output_path=output_path)
    normalized_event_type = normalize_event_type(event_type)
    initialize_database(output_path)
    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(get_database_path(output_path)) as connection:
        if dedupe:
            existing_event = connection.execute(
                """
                SELECT id
                FROM lead_events
                WHERE file_name = ? AND event_type = ?
                LIMIT 1
                """,
                (file_name, normalized_event_type),
            ).fetchone()
            if existing_event:
                return {
                    "id": existing_event[0],
                    "file_name": file_name,
                    "event_type": normalized_event_type,
                    "event_label": event_label,
                    "event_detail": event_detail,
                    "created_at": created_at,
                }

        cursor = connection.execute(
            """
            INSERT INTO lead_events (
                file_name,
                event_type,
                event_label,
                event_detail,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                file_name,
                normalized_event_type,
                event_label,
                event_detail,
                created_at,
            ),
        )

    return {
        "id": cursor.lastrowid,
        "file_name": file_name,
        "event_type": normalized_event_type,
        "event_label": event_label,
        "event_detail": event_detail,
        "created_at": created_at,
    }


def list_lead_events(
    file_name: str,
    output_dir: str | Path = "data/outputs",
) -> list[dict[str, Any]]:
    """Return audit events for one saved lead."""
    output_path = Path(output_dir)
    get_safe_output_file_path(file_name=file_name, output_path=output_path)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                file_name,
                event_type,
                event_label,
                event_detail,
                created_at
            FROM lead_events
            WHERE file_name = ?
            ORDER BY created_at DESC, id DESC
            """,
            (file_name,),
        ).fetchall()

    return [dict(row) for row in rows]


def has_lead_event(
    file_name: str,
    event_type: str,
    output_dir: str | Path = "data/outputs",
) -> bool:
    """Return whether a saved lead already has a matching audit event."""
    output_path = Path(output_dir)
    get_safe_output_file_path(file_name=file_name, output_path=output_path)
    normalized_event_type = normalize_event_type(event_type)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            """
            SELECT id
            FROM lead_events
            WHERE file_name = ? AND event_type = ?
            LIMIT 1
            """,
            (file_name, normalized_event_type),
        ).fetchone()

    return row is not None


def has_exported_lead_to_google_sheets(
    lead_id: str,
    output_dir: str | Path = "data/outputs",
) -> bool:
    """Return whether any saved output for this lead was exported to Google Sheets."""
    normalized_lead_id = str(lead_id or "").strip()
    if not normalized_lead_id:
        return False

    output_path = Path(output_dir)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            """
            SELECT lead_events.id
            FROM lead_events
            INNER JOIN saved_leads
                ON saved_leads.file_name = lead_events.file_name
            WHERE saved_leads.lead_id = ?
                AND lead_events.event_type = ?
            LIMIT 1
            """,
            (normalized_lead_id, "google_sheets_exported"),
        ).fetchone()

    return row is not None


def has_exported_email_to_google_sheets(
    email: str,
    output_dir: str | Path = "data/outputs",
) -> bool:
    """Return whether any saved output for this email was exported to Google Sheets."""
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return False

    output_path = Path(output_dir)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            """
            SELECT lead_events.id
            FROM lead_events
            INNER JOIN saved_leads
                ON saved_leads.file_name = lead_events.file_name
            WHERE lower(saved_leads.email) = ?
                AND lead_events.event_type = ?
            LIMIT 1
            """,
            (normalized_email, "google_sheets_exported"),
        ).fetchone()

    return row is not None


def normalize_event_type(event_type: str) -> str:
    """Return a supported audit event type."""
    normalized_event_type = str(event_type or "").strip().lower()
    if normalized_event_type not in VALID_EVENT_TYPES:
        raise ValueError("Event type must be one of: " + ", ".join(sorted(VALID_EVENT_TYPES)))

    return normalized_event_type


def normalize_integration_provider(provider: str) -> str:
    """Return a normalized integration provider identifier."""
    normalized_provider = str(provider or "").strip().lower()
    if not normalized_provider:
        raise ValueError("Integration provider is required.")

    return normalized_provider


def normalize_integration_run_status(status: str) -> str:
    """Return a supported integration run status."""
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in VALID_INTEGRATION_RUN_STATUSES:
        raise ValueError(
            "Integration run status must be one of: "
            + ", ".join(sorted(VALID_INTEGRATION_RUN_STATUSES))
        )

    return normalized_status


def normalize_review_status(review_status: str) -> str:
    """Return a supported review status."""
    normalized_status = str(review_status or "new").strip().lower()
    if normalized_status not in VALID_REVIEW_STATUSES:
        raise ValueError("Review status must be one of: " + ", ".join(sorted(VALID_REVIEW_STATUSES)))

    return normalized_status


def load_saved_output_from_database(
    file_name: str,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Any] | None:
    """Load one saved result from SQLite if it exists."""
    output_path = Path(output_dir)
    get_safe_output_file_path(file_name=file_name, output_path=output_path)
    sync_json_outputs_to_database(output_dir=output_path)

    with sqlite3.connect(get_database_path(output_path)) as connection:
        row = connection.execute(
            "SELECT result_json FROM saved_leads WHERE file_name = ?",
            (file_name,),
        ).fetchone()

    if not row:
        return None

    return json.loads(row[0])


def build_history_csv(history_rows: list[dict[str, Any]]) -> str:
    """Build a CSV export from saved lead history rows."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=HISTORY_CSV_COLUMNS)
    writer.writeheader()

    for row in history_rows:
        writer.writerow(
            {column: row.get(column, "") for column in HISTORY_CSV_COLUMNS}
        )

    return output.getvalue()


def build_history_row(result: dict[str, Any], file_path: Path) -> dict[str, Any]:
    """Build one compact row for history and future exports."""
    lead = result.get("lead", {})
    contact = lead.get("contact", {})
    lead_details = lead.get("lead_details", {})
    ai_outputs = result.get("ai_outputs", {})
    score = ai_outputs.get("score", {})
    crm_ready = result.get("crm_ready", {})

    contact_name = crm_ready.get("contact_name") or (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    )

    return {
        "file_name": file_path.name,
        "output_path": str(file_path),
        "processed_at": crm_ready.get("processed_at", result.get("processed_at", "")),
        "lead_id": crm_ready.get("lead_id", lead.get("lead_id", "")),
        "contact_name": contact_name,
        "company": crm_ready.get("company", contact.get("company", "")),
        "email": crm_ready.get("email", contact.get("email", "")),
        "business_type": crm_ready.get("business_type", lead.get("business_type", "")),
        "service_interest": crm_ready.get(
            "service_interest",
            lead_details.get("service_interest", ""),
        ),
        "classification": crm_ready.get(
            "classification",
            ai_outputs.get("classification", ""),
        ),
        "lead_score": crm_ready.get("lead_score", score.get("total_score", "")),
        "max_score": crm_ready.get("max_score", score.get("max_score", "")),
        "lead_rating": crm_ready.get("lead_rating", score.get("rating", "")),
        "review_status": crm_ready.get("review_status", "new"),
        "recommended_next_action": crm_ready.get(
            "recommended_next_action",
            get_recommended_next_action(ai_outputs.get("classification", "")),
        ),
    }


def build_result(
    lead: dict[str, Any],
    summary: str,
    classification: str,
    score: dict[str, Any],
    follow_up_message: str,
) -> dict[str, Any]:
    """Build the final automation result that will be saved locally."""
    processed_at = datetime.now(timezone.utc).isoformat()
    ai_metadata = build_ai_metadata(processed_at)

    return {
        "processed_at": processed_at,
        "lead": lead,
        "ai_outputs": {
            "summary": summary,
            "classification": classification,
            "score": score,
            "follow_up_message": follow_up_message,
            "metadata": ai_metadata,
        },
        "metadata": {
            "workflow_version": WORKFLOW_VERSION,
            "processed_at": processed_at,
            "ai": ai_metadata,
        },
        "crm_ready": build_crm_ready_output(
            lead=lead,
            summary=summary,
            classification=classification,
            score=score,
            follow_up_message=follow_up_message,
            processed_at=processed_at,
            ai_metadata=ai_metadata,
        ),
    }


def build_ai_metadata(processed_at: str) -> dict[str, Any]:
    """Build AI model and prompt-version metadata for one workflow run."""
    return {
        "model": OPENAI_MODEL,
        "workflow_version": WORKFLOW_VERSION,
        "summary_prompt_version": SUMMARY_PROMPT_VERSION,
        "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
        "follow_up_prompt_version": FOLLOW_UP_PROMPT_VERSION,
        "summary_generated_at": processed_at,
        "classification_generated_at": processed_at,
        "follow_up_generated_at": processed_at,
    }


def build_crm_ready_output(
    lead: dict[str, Any],
    summary: str,
    classification: str,
    score: dict[str, Any],
    follow_up_message: str,
    processed_at: str,
    ai_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a flatter output shape for CRM or spreadsheet handoff."""
    contact = lead["contact"]
    lead_details = lead["lead_details"]
    full_name = f"{contact['first_name']} {contact['last_name']}".strip()

    return {
        "lead_id": lead["lead_id"],
        "source": lead["source"],
        "submitted_at": lead["submitted_at"],
        "processed_at": processed_at,
        "contact_name": full_name,
        "email": contact["email"],
        "phone": contact["phone"],
        "company": contact["company"],
        "business_type": lead["business_type"],
        "service_interest": lead_details["service_interest"],
        "preferred_contact_method": lead_details["preferred_contact_method"],
        "classification": classification,
        "lead_score": score["total_score"],
        "max_score": score["max_score"],
        "lead_rating": score["rating"],
        "score_breakdown": score["breakdown"],
        "recommended_next_action": get_recommended_next_action(classification),
        "summary": summary,
        "follow_up_message": follow_up_message,
        "ai_metadata": ai_metadata,
    }


def get_recommended_next_action(classification: str) -> str:
    """Map lead classification to a practical sales follow-up action."""
    normalized_classification = classification.lower()

    if normalized_classification == "hot":
        return "Reply quickly and offer a discovery call or product walkthrough."

    if normalized_classification == "warm":
        return "Send helpful details and ask a qualifying follow-up question."

    return "Add to nurture list and follow up with educational content."
