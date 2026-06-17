"""FastAPI webhook endpoints for the AI Lead Intake Automation System."""

import json
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.automation.logger import log_structured_event, setup_logger
from app.automation.storage import (
    archive_saved_output,
    build_history_csv,
    bulk_update_review_status,
    create_integration_run,
    get_integration_run,
    get_integration_status_summary,
    has_exported_email_to_google_sheets,
    has_exported_lead_to_google_sheets,
    has_lead_event,
    list_integration_runs,
    list_lead_events,
    list_saved_outputs,
    load_idempotency_response,
    load_saved_output,
    record_lead_event,
    save_idempotency_response,
    update_integration_run_after_retry,
    update_review_status,
)
from app.automation.workflow import process_lead
from app.config import (
    AIRTABLE_ENABLED,
    GOOGLE_SHEETS_AUTO_APPEND,
    HUBSPOT_ENABLED,
    WEBHOOK_API_KEYS,
    WEBHOOK_AUTH_ENABLED,
    WEBHOOK_HMAC_ENABLED,
    WEBHOOK_HMAC_SECRET,
    WEBHOOK_REPLAY_PROTECTION_ENABLED,
    WEBHOOK_SIGNATURE_TOLERANCE_SECONDS,
)
from app.integrations.google_sheets import (
    GOOGLE_SHEETS_COLUMNS,
    GoogleSheetsAppendError,
    GoogleSheetsConfigError,
    append_result_to_google_sheet,
    build_google_sheets_payload,
    build_google_sheets_row,
)
from app.integrations.dispatcher import (
    build_legacy_google_sheets_response,
    dispatch_processed_lead_integrations,
    extract_destination_message,
    extract_external_id,
    retry_integration_destination,
)
from app.history_page import render_history_detail_page, render_history_page
from app.lead_intake_page import render_lead_intake_page
from app.operations import build_operations_status, render_system_status_page
from app.privacy import is_masked_mode
from app.rate_limiter import (
    build_rate_limit_headers,
    get_rate_limit_key,
    lead_process_rate_limiter,
)
from app.security.webhook_auth import (
    API_KEY_ERROR_DETAIL,
    HMAC_ERROR_DETAIL,
    HMAC_NOT_CONFIGURED_DETAIL,
    is_valid_api_key,
    is_valid_hmac_signature,
)


STATIC_DIR = Path(__file__).parent / "static"
AI_PROCESSING_UNAVAILABLE_DETAIL = (
    "AI processing is unavailable right now. The lead was not processed because "
    "the AI service could not be reached or is not configured correctly. Please "
    "check the server configuration and try again."
)

app = FastAPI(
    title="AI Lead Intake Automation API",
    description="Webhook API for processing and qualifying inbound leads.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger = setup_logger()


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next: Any) -> Response:
    """Add request IDs and structured request logs to every API response."""
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as error:
        log_structured_event(
            logger=logger,
            event="api_request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
            error_type=type(error).__name__,
            error=str(error),
        )
        raise
    finally:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        if "response" in locals():
            response.headers["X-Request-ID"] = request_id

        log_structured_event(
            logger=logger,
            event="api_request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_host=request.client.host if request.client else "",
        )


@app.get("/", response_class=HTMLResponse)
def lead_intake_home() -> str:
    """Serve the browser-based lead intake workspace."""
    return render_lead_intake_page()


@app.get("/lead-intake", response_class=HTMLResponse)
def lead_intake_page() -> str:
    """Serve the browser-based lead intake workspace."""
    return render_lead_intake_page()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple API health check."""
    return {"status": "ok"}


@app.get("/health/details")
def detailed_health_check() -> dict[str, Any]:
    """Return detailed operational readiness checks."""
    return build_operations_status()


@app.get("/system-status", response_class=HTMLResponse)
def system_status_page() -> str:
    """Serve a browser page with operational readiness details."""
    return render_system_status_page(build_operations_status())


@app.get("/history", response_class=HTMLResponse)
def lead_history_page(
    classification: str = "all",
    status: str = "all",
    sort: str = "newest",
    search: str = "",
    page: int = 1,
) -> str:
    """Serve a browser page for reviewing saved processed leads."""
    return render_history_page(
        history_rows=list_saved_outputs(),
        selected_classification=classification,
        selected_status=status,
        selected_sort=sort,
        search_query=search,
        page=page,
    )


@app.get("/api/history")
def lead_history_api() -> dict[str, Any]:
    """Return saved processed lead history as JSON."""
    return {"leads": list_saved_outputs()}


@app.post("/api/history/bulk-status")
def bulk_update_lead_review_status(payload: dict[str, Any]) -> dict[str, Any]:
    """Update review status for several saved leads."""
    file_names = payload.get("file_names", [])
    if not isinstance(file_names, list):
        raise HTTPException(status_code=400, detail="file_names must be a list.")

    try:
        result = bulk_update_review_status(
            file_names=[str(file_name) for file_name in file_names],
            review_status=str(payload.get("review_status", "")),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"status": "updated", **result}


@app.get("/history/export.csv")
def lead_history_csv_export() -> Response:
    """Download saved processed lead history as a CSV file."""
    history_rows = list_saved_outputs()
    csv_content = build_history_csv(history_rows)

    for row in history_rows:
        try:
            record_lead_event(
                file_name=row["file_name"],
                event_type="csv_exported",
                event_label="CSV exported",
                event_detail="Lead included in history CSV export.",
            )
        except ValueError:
            continue

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="lead-history.csv"',
        },
    )


@app.get("/history/{file_name}", response_class=HTMLResponse)
def lead_history_detail_page(file_name: str, privacy: str = "") -> str:
    """Serve a browser page for reviewing one saved processed lead."""
    try:
        result = load_saved_output(file_name)
        record_lead_event(
            file_name=file_name,
            event_type="lead_viewed",
            event_label="Lead detail viewed",
            event_detail="Saved lead detail page opened.",
        )
        events = list_lead_events(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return render_history_detail_page(
        result=result,
        file_name=file_name,
        events=events,
        masked=is_masked_mode(privacy),
    )


@app.get("/api/history/{file_name}")
def lead_history_detail_api(file_name: str) -> dict[str, Any]:
    """Return one saved processed lead result as JSON."""
    try:
        return load_saved_output(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/history/{file_name}/events")
def lead_history_events_api(file_name: str) -> dict[str, Any]:
    """Return audit events for one saved processed lead."""
    try:
        return {"events": list_lead_events(file_name)}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/integrations/google-sheets/preview")
def google_sheets_history_preview() -> dict[str, Any]:
    """Return Google Sheets-ready rows for saved lead history."""
    rows = []

    for history_row in list_saved_outputs():
        try:
            result = load_saved_output(history_row["file_name"])
        except (ValueError, FileNotFoundError):
            continue
        rows.append(build_google_sheets_row(result))

    return {
        "integration": "google_sheets",
        "columns": GOOGLE_SHEETS_COLUMNS,
        "rows": rows,
    }


@app.get("/api/integrations/runs")
def integration_runs_api(
    file_name: str | None = None,
    lead_id: str | None = None,
    provider: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Return safe downstream integration run history."""
    try:
        runs = list_integration_runs(
            file_name=file_name,
            lead_id=lead_id,
            provider=provider,
            status=status,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"runs": runs}


@app.get("/api/integrations/status")
def integration_status_api() -> dict[str, Any]:
    """Return provider enablement and integration run health summary."""
    run_summary = get_integration_status_summary()
    provider_enabled = {
        "google_sheets": GOOGLE_SHEETS_AUTO_APPEND,
        "airtable": AIRTABLE_ENABLED,
        "hubspot": HUBSPOT_ENABLED,
    }
    providers = {}

    for provider, enabled in provider_enabled.items():
        provider_summary = run_summary.get(provider, {})
        providers[provider] = {
            "enabled": bool(enabled),
            "last_status": provider_summary.get("last_status")
            or ("disabled" if not enabled else "not_run"),
            "success_count": int(provider_summary.get("success_count", 0)),
            "failed_count": int(provider_summary.get("failed_count", 0)),
            "skipped_count": int(provider_summary.get("skipped_count", 0)),
        }

    return {
        "providers": providers,
        "failed_total": sum(
            provider_summary["failed_count"]
            for provider_summary in providers.values()
        ),
    }


@app.post("/api/integrations/retry/{run_id}")
def retry_integration_run_api(run_id: int) -> dict[str, Any]:
    """Retry one failed downstream integration run."""
    integration_run = get_integration_run(run_id)
    if integration_run is None:
        raise HTTPException(status_code=404, detail="Integration run not found.")

    if integration_run.get("status") != "failed":
        raise HTTPException(
            status_code=400,
            detail="Only failed integration runs can be retried.",
        )

    file_name = str(integration_run.get("file_name") or "")
    try:
        processed_lead = load_saved_output(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    retry_result = retry_integration_destination(
        provider=str(integration_run.get("provider") or ""),
        processed_lead=processed_lead,
        output_path=str(Path("data/outputs") / file_name),
        google_sheets_auto_append=GOOGLE_SHEETS_AUTO_APPEND,
        airtable_enabled=AIRTABLE_ENABLED,
        hubspot_enabled=HUBSPOT_ENABLED,
        duplicate_export_checker=find_google_sheets_duplicate_export,
        append_google_sheets_result=append_result_to_google_sheet,
        record_event=record_lead_event,
        event_logger=logger,
    )
    retry_status = normalize_retry_status(retry_result)

    try:
        update_integration_run_after_retry(
            run_id=run_id,
            status=retry_status,
            external_id=extract_external_id(retry_result),
            message=extract_destination_message(retry_result),
            response_json=retry_result,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    updated_run = get_integration_run(run_id) or integration_run

    return {
        "status": retry_status,
        "run_id": run_id,
        "provider": integration_run.get("provider"),
        "retry_count": updated_run.get("retry_count", 0),
        "result": retry_result,
    }


@app.get("/api/integrations/google-sheets/preview/{file_name}")
def google_sheets_lead_preview(file_name: str) -> dict[str, Any]:
    """Return a Google Sheets append payload preview for one saved lead."""
    try:
        result = load_saved_output(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return {
        "integration": "google_sheets",
        "payload": build_google_sheets_payload(result),
    }


@app.post("/api/integrations/google-sheets/append/{file_name}")
def google_sheets_append_saved_lead(file_name: str) -> dict[str, Any]:
    """Append one saved lead result to the configured live Google Sheet."""
    try:
        result = load_saved_output(file_name)
        duplicate_export = find_google_sheets_duplicate_export(
            result=result,
            file_name=file_name,
        )
        if duplicate_export:
            return {
                "integration": "google_sheets",
                "file_name": file_name,
                "result": {
                    "status": "skipped",
                    "reason": "already_exported",
                    "detail": duplicate_export,
                },
            }

        append_result = append_result_to_google_sheet(result)
        record_lead_event(
            file_name=file_name,
            event_type="google_sheets_exported",
            event_label="Exported to Google Sheets",
            event_detail=append_result.get("updated_range", ""),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except GoogleSheetsConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except GoogleSheetsAppendError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        "integration": "google_sheets",
        "file_name": file_name,
        "result": append_result,
    }


@app.post("/api/history/{file_name}/status")
def update_lead_review_status(file_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Update one saved lead review status."""
    try:
        row = update_review_status(
            file_name=file_name,
            review_status=str(payload.get("review_status", "")),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return {"status": "updated", "lead": row}


@app.post("/api/history/{file_name}/archive")
def archive_lead_history_item(file_name: str) -> dict[str, Any]:
    """Archive one saved lead while preserving its audit trail."""
    try:
        row = archive_saved_output(file_name=file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return {"status": "archived", "lead": row}


@app.post("/api/history/{file_name}/events")
def record_lead_history_event(file_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Record one audit event for a saved processed lead."""
    try:
        event = record_lead_event(
            file_name=file_name,
            event_type=str(payload.get("event_type", "")),
            event_label=str(payload.get("event_label", "")),
            event_detail=str(payload.get("event_detail", "")),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return {"status": "recorded", "event": event}


@app.post("/webhooks/leads")
async def process_lead_webhook(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    """Process one lead from a webhook-style JSON request body."""
    raw_body = await request.body()
    authenticate_webhook_request(request=request, raw_body=raw_body)

    idempotency_key = request.headers.get("Idempotency-Key", "").strip()
    if idempotency_key:
        saved_response = load_idempotency_response(idempotency_key)
        if saved_response is not None:
            return saved_response

    rate_limit_result = lead_process_rate_limiter.check(get_rate_limit_key(request))
    for header, value in build_rate_limit_headers(rate_limit_result).items():
        response.headers[header] = value

    if not rate_limit_result.allowed:
        log_structured_event(
            logger=logger,
            event="lead_process_rate_limited",
            client_key=get_rate_limit_key(request),
            limit=rate_limit_result.limit,
            retry_after_seconds=rate_limit_result.retry_after_seconds,
        )
        raise HTTPException(
            status_code=429,
            detail="Lead processing rate limit exceeded. Try again later.",
            headers=build_rate_limit_headers(rate_limit_result),
        )

    try:
        lead = json.loads(raw_body)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from error

    try:
        result, output_path = process_lead(lead)
    except ValueError as error:
        logger.error("Webhook validation error: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        request_id = getattr(request.state, "request_id", "")
        log_structured_event(
            logger=logger,
            event="lead_process_ai_failed",
            request_id=request_id,
            error_type=type(error).__name__,
            error=str(error),
        )
        raise HTTPException(
            status_code=502,
            detail=build_client_processing_error_detail(request),
        ) from error
    except Exception as error:
        logger.exception("Unexpected webhook error")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while processing lead.",
        ) from error

    integration_result = dispatch_processed_lead_integrations(
        result=result,
        output_path=str(output_path),
        google_sheets_auto_append=GOOGLE_SHEETS_AUTO_APPEND,
        airtable_enabled=AIRTABLE_ENABLED,
        hubspot_enabled=HUBSPOT_ENABLED,
        duplicate_export_checker=find_google_sheets_duplicate_export,
        append_google_sheets_result=append_result_to_google_sheet,
        record_event=record_lead_event,
        record_integration_runs=True,
        integration_run_recorder=create_integration_run,
        event_logger=logger,
    )
    google_sheets_result = build_legacy_google_sheets_response(integration_result)

    response_payload = {
        "status": "processed",
        "output_path": str(output_path),
        "result": result,
    }
    if google_sheets_result:
        response_payload["google_sheets"] = google_sheets_result

    if idempotency_key:
        save_idempotency_response(
            idempotency_key=idempotency_key,
            response_payload=response_payload,
            lead_id=result.get("lead", {}).get("lead_id", ""),
            file_name=Path(output_path).name,
        )

    return response_payload


def authenticate_webhook_request(request: Request, raw_body: bytes) -> None:
    """Validate configured webhook authentication requirements."""
    if WEBHOOK_AUTH_ENABLED and not is_valid_api_key(
        request.headers.get("X-API-Key"),
        WEBHOOK_API_KEYS,
    ):
        raise HTTPException(status_code=401, detail=API_KEY_ERROR_DETAIL)

    if not WEBHOOK_HMAC_ENABLED:
        return

    if not WEBHOOK_HMAC_SECRET:
        log_structured_event(
            logger=logger,
            event="webhook_hmac_not_configured",
            request_id=getattr(request.state, "request_id", ""),
        )
        raise HTTPException(status_code=500, detail=HMAC_NOT_CONFIGURED_DETAIL)

    if not is_valid_hmac_signature(
        raw_body=raw_body,
        timestamp=request.headers.get("X-Webhook-Timestamp"),
        signature=request.headers.get("X-Webhook-Signature"),
        secret=WEBHOOK_HMAC_SECRET,
        tolerance_seconds=WEBHOOK_SIGNATURE_TOLERANCE_SECONDS,
        replay_protection_enabled=WEBHOOK_REPLAY_PROTECTION_ENABLED,
    ):
        raise HTTPException(status_code=401, detail=HMAC_ERROR_DETAIL)


def find_google_sheets_duplicate_export(
    result: dict[str, Any],
    file_name: str,
) -> str:
    """Return a duplicate-export reason if this lead was already exported."""
    if has_lead_event(file_name, "google_sheets_exported"):
        return "This saved lead file has already been exported to Google Sheets."

    email = result.get("crm_ready", {}).get("email") or result.get("lead", {}).get("contact", {}).get("email", "")
    if has_exported_email_to_google_sheets(email):
        return "A saved result with this email has already been exported to Google Sheets."

    lead_id = result.get("crm_ready", {}).get("lead_id") or result.get("lead", {}).get("lead_id", "")
    if has_exported_lead_to_google_sheets(lead_id):
        return "A saved result with this lead ID has already been exported to Google Sheets."

    return ""


def build_client_processing_error_detail(request: Request) -> str:
    """Return a browser-safe lead-processing error message."""
    request_id = getattr(request.state, "request_id", "")
    if not request_id:
        return AI_PROCESSING_UNAVAILABLE_DETAIL

    return f"{AI_PROCESSING_UNAVAILABLE_DETAIL} Reference ID: {request_id}"


def normalize_retry_status(retry_result: dict[str, Any]) -> str:
    """Return the integration run status to store after a retry attempt."""
    status = str(retry_result.get("status", "")).strip().lower()
    if status in {"success", "skipped"}:
        return status

    return "failed"
