"""Dispatch processed leads to configured downstream integrations."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.automation.logger import log_structured_event, setup_logger
from app.automation.storage import (
    create_integration_run,
    has_exported_email_to_google_sheets,
    has_exported_lead_to_google_sheets,
    has_lead_event,
    record_lead_event,
)
from app.config import AIRTABLE_ENABLED, GOOGLE_SHEETS_AUTO_APPEND, HUBSPOT_ENABLED
from app.integrations.airtable import (
    AirtableConfigError,
    AirtableDeliveryError,
    send_processed_lead_to_airtable,
)
from app.integrations.google_sheets import (
    GoogleSheetsAppendError,
    GoogleSheetsConfigError,
    append_result_to_google_sheet,
)
from app.integrations.hubspot import (
    HubSpotConfigError,
    HubSpotDeliveryError,
    send_processed_lead_to_hubspot,
)


logger = setup_logger()


def dispatch_processed_lead_integrations(
    *,
    result: dict[str, Any],
    output_path: str,
    google_sheets_auto_append: bool = GOOGLE_SHEETS_AUTO_APPEND,
    airtable_enabled: bool = AIRTABLE_ENABLED,
    hubspot_enabled: bool = HUBSPOT_ENABLED,
    duplicate_export_checker: Callable[[dict[str, Any], str], str] | None = None,
    append_google_sheets_result: Callable[[dict[str, Any]], dict[str, Any]] = append_result_to_google_sheet,
    send_airtable_record: Callable[..., dict[str, Any]] = send_processed_lead_to_airtable,
    send_hubspot_contact: Callable[..., dict[str, Any]] = send_processed_lead_to_hubspot,
    record_event: Callable[..., dict[str, Any]] = record_lead_event,
    record_integration_runs: bool = False,
    integration_run_recorder: Callable[..., int] = create_integration_run,
    output_dir: str | Path | None = None,
    event_logger: Any = logger,
) -> dict[str, Any]:
    """Dispatch one processed lead to enabled downstream integrations."""
    file_name = Path(output_path).name
    google_sheets_result = dispatch_google_sheets_destination(
        result=result,
        output_path=output_path,
        file_name=file_name,
        enabled=google_sheets_auto_append,
        duplicate_export_checker=duplicate_export_checker or find_google_sheets_duplicate_export,
        append_google_sheets_result=append_google_sheets_result,
        record_event=record_event,
        event_logger=event_logger,
    )
    airtable_result = dispatch_airtable_destination(
        result=result,
        output_path=output_path,
        enabled=airtable_enabled,
        send_airtable_record=send_airtable_record,
        event_logger=event_logger,
    )
    hubspot_result = dispatch_hubspot_destination(
        result=result,
        enabled=hubspot_enabled,
        send_hubspot_contact=send_hubspot_contact,
        event_logger=event_logger,
    )
    destinations = {
        "google_sheets": google_sheets_result,
        "airtable": airtable_result,
        "hubspot": hubspot_result,
    }

    if record_integration_runs:
        record_destination_runs(
            destinations=destinations,
            result=result,
            file_name=file_name,
            recorder=integration_run_recorder,
            output_dir=output_dir,
        )

    return {
        "destinations": destinations,
    }


def record_destination_runs(
    *,
    destinations: dict[str, dict[str, Any]],
    result: dict[str, Any],
    file_name: str,
    recorder: Callable[..., int],
    output_dir: str | Path | None = None,
) -> None:
    """Record meaningful downstream destination outcomes."""
    lead_id = result.get("crm_ready", {}).get("lead_id") or result.get("lead", {}).get("lead_id")

    for provider, destination_result in destinations.items():
        status = str(destination_result.get("status", "")).strip().lower()
        if status not in {"success", "failed", "skipped"}:
            continue

        recorder(
            file_name=file_name,
            lead_id=lead_id,
            provider=provider,
            status=status,
            external_id=extract_external_id(destination_result),
            message=extract_destination_message(destination_result),
            response_json=destination_result,
            output_dir=output_dir,
        )


def dispatch_google_sheets_destination(
    *,
    result: dict[str, Any],
    output_path: str,
    file_name: str,
    enabled: bool,
    duplicate_export_checker: Callable[[dict[str, Any], str], str],
    append_google_sheets_result: Callable[[dict[str, Any]], dict[str, Any]],
    record_event: Callable[..., dict[str, Any]],
    event_logger: Any = logger,
) -> dict[str, Any]:
    """Append a processed lead to Google Sheets when webhook auto-append is enabled."""
    if not enabled:
        return {"status": "disabled"}

    duplicate_export = duplicate_export_checker(result, file_name)
    if duplicate_export:
        return {
            "status": "skipped",
            "reason": "already_exported",
            "detail": duplicate_export,
        }

    try:
        append_result = append_google_sheets_result(result)
        record_event(
            file_name=file_name,
            event_type="google_sheets_exported",
            event_label="Auto-exported to Google Sheets",
            event_detail=append_result.get("updated_range", ""),
        )
    except (GoogleSheetsConfigError, GoogleSheetsAppendError) as error:
        log_structured_event(
            logger=event_logger,
            event="google_sheets_auto_append_failed",
            output_path=output_path,
            error_type=type(error).__name__,
            error=str(error),
        )
        return {
            "status": "failed",
            "error": str(error),
            "detail": str(error),
        }

    return {
        "status": "success",
        "result": append_result,
    }


def dispatch_airtable_destination(
    *,
    result: dict[str, Any],
    output_path: str,
    enabled: bool,
    send_airtable_record: Callable[..., dict[str, Any]],
    event_logger: Any = logger,
) -> dict[str, Any]:
    """Send a processed lead to Airtable when the destination is enabled."""
    if not enabled:
        return {"status": "disabled"}

    try:
        airtable_result = send_airtable_record(
            processed_lead=result,
            output_path=output_path,
            enabled=enabled,
        )
    except (AirtableConfigError, AirtableDeliveryError) as error:
        log_structured_event(
            logger=event_logger,
            event="airtable_delivery_failed",
            output_path=output_path,
            error_type=type(error).__name__,
            error=str(error),
        )
        return {
            "status": "failed",
            "error": str(error),
        }

    return {
        "status": "success",
        "result": airtable_result,
    }


def dispatch_hubspot_destination(
    *,
    result: dict[str, Any],
    enabled: bool,
    send_hubspot_contact: Callable[..., dict[str, Any]],
    event_logger: Any = logger,
) -> dict[str, Any]:
    """Send a processed lead to HubSpot when the destination is enabled."""
    if not enabled:
        return {"status": "disabled"}

    try:
        hubspot_result = send_hubspot_contact(
            processed_lead=result,
            enabled=enabled,
        )
    except (HubSpotConfigError, HubSpotDeliveryError) as error:
        log_structured_event(
            logger=event_logger,
            event="hubspot_delivery_failed",
            error_type=type(error).__name__,
            error=str(error),
        )
        return {
            "status": "failed",
            "error": str(error),
        }

    return {
        "status": "success",
        "result": hubspot_result,
    }


def retry_integration_destination(
    *,
    provider: str,
    processed_lead: dict[str, Any],
    output_path: str = "",
    google_sheets_auto_append: bool = GOOGLE_SHEETS_AUTO_APPEND,
    airtable_enabled: bool = AIRTABLE_ENABLED,
    hubspot_enabled: bool = HUBSPOT_ENABLED,
    duplicate_export_checker: Callable[[dict[str, Any], str], str] | None = None,
    append_google_sheets_result: Callable[[dict[str, Any]], dict[str, Any]] = append_result_to_google_sheet,
    send_airtable_record: Callable[..., dict[str, Any]] = send_processed_lead_to_airtable,
    send_hubspot_contact: Callable[..., dict[str, Any]] = send_processed_lead_to_hubspot,
    record_event: Callable[..., dict[str, Any]] = record_lead_event,
    event_logger: Any = logger,
) -> dict[str, Any]:
    """Retry one configured downstream integration destination."""
    normalized_provider = str(provider or "").strip().lower()
    file_name = Path(output_path).name if output_path else ""

    if normalized_provider == "google_sheets":
        if not google_sheets_auto_append:
            return {"status": "failed", "error": "Google Sheets integration is disabled."}
        return dispatch_google_sheets_destination(
            result=processed_lead,
            output_path=output_path or file_name,
            file_name=file_name,
            enabled=True,
            duplicate_export_checker=duplicate_export_checker or find_google_sheets_duplicate_export,
            append_google_sheets_result=append_google_sheets_result,
            record_event=record_event,
            event_logger=event_logger,
        )

    if normalized_provider == "airtable":
        if not airtable_enabled:
            return {"status": "failed", "error": "Airtable integration is disabled."}
        return dispatch_airtable_destination(
            result=processed_lead,
            output_path=output_path or file_name,
            enabled=True,
            send_airtable_record=send_airtable_record,
            event_logger=event_logger,
        )

    if normalized_provider == "hubspot":
        if not hubspot_enabled:
            return {"status": "failed", "error": "HubSpot integration is disabled."}
        return dispatch_hubspot_destination(
            result=processed_lead,
            enabled=True,
            send_hubspot_contact=send_hubspot_contact,
            event_logger=event_logger,
        )

    return {
        "status": "failed",
        "error": "Unknown integration provider.",
    }


def build_legacy_google_sheets_response(
    integration_result: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the existing webhook google_sheets response shape."""
    google_sheets_result = integration_result.get("destinations", {}).get("google_sheets", {})
    status = google_sheets_result.get("status")

    if status == "disabled":
        return None

    if status == "success":
        return google_sheets_result.get("result", {})

    if status in {"skipped", "failed"}:
        legacy_result = dict(google_sheets_result)
        legacy_result.pop("error", None)
        return legacy_result

    return None


def extract_external_id(destination_result: dict[str, Any]) -> str | None:
    """Return a stable external identifier from a destination result when present."""
    nested_result = destination_result.get("result")
    if not isinstance(nested_result, dict):
        return None

    for key in ("record_id", "object_id", "spreadsheet_id", "id"):
        value = nested_result.get(key)
        if value:
            return str(value)

    return None


def extract_destination_message(destination_result: dict[str, Any]) -> str | None:
    """Return a safe status message for run history."""
    for key in ("error", "detail", "reason"):
        value = destination_result.get(key)
        if value:
            return str(value)

    status = destination_result.get("status")
    return str(status) if status else None


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
