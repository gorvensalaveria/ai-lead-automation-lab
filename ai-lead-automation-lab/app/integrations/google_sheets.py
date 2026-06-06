"""Google Sheets handoff payload builder and live append client."""

import json
from typing import Any
from urllib.parse import quote, urlencode

import requests

from app.config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_SHEETS_ENABLED,
    GOOGLE_SHEETS_INSERT_DATA_OPTION,
    GOOGLE_SHEETS_RANGE,
    GOOGLE_SHEETS_SPREADSHEET_ID,
    GOOGLE_SHEETS_VALUE_INPUT_OPTION,
)


GOOGLE_SHEETS_COLUMNS = [
    "processed_at",
    "lead_id",
    "contact_name",
    "company",
    "email",
    "phone",
    "business_type",
    "service_interest",
    "classification",
    "lead_score",
    "max_score",
    "lead_rating",
    "review_status",
    "recommended_next_action",
    "summary",
    "follow_up_message",
    "source",
    "preferred_contact_method",
    "workflow_version",
    "model",
]
GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_SHEETS_API_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"


class GoogleSheetsConfigError(RuntimeError):
    """Raised when the live Google Sheets integration is not configured."""


class GoogleSheetsAppendError(RuntimeError):
    """Raised when a live Google Sheets append request fails."""


def build_google_sheets_row(result: dict[str, Any]) -> dict[str, Any]:
    """Build one flat row ready for Google Sheets append APIs."""
    lead = result.get("lead", {})
    contact = lead.get("contact", {})
    ai_outputs = result.get("ai_outputs", {})
    crm_ready = result.get("crm_ready", {})
    ai_metadata = get_ai_metadata(result)

    row = {
        "processed_at": crm_ready.get("processed_at", result.get("processed_at", "")),
        "lead_id": crm_ready.get("lead_id", lead.get("lead_id", "")),
        "contact_name": crm_ready.get("contact_name", ""),
        "company": crm_ready.get("company", contact.get("company", "")),
        "email": crm_ready.get("email", contact.get("email", "")),
        "phone": crm_ready.get("phone", contact.get("phone", "")),
        "business_type": crm_ready.get("business_type", lead.get("business_type", "")),
        "service_interest": crm_ready.get("service_interest", ""),
        "classification": crm_ready.get("classification", ai_outputs.get("classification", "")),
        "lead_score": crm_ready.get("lead_score", ""),
        "max_score": crm_ready.get("max_score", ""),
        "lead_rating": crm_ready.get("lead_rating", ""),
        "review_status": crm_ready.get("review_status", result.get("review_status", "new")),
        "recommended_next_action": crm_ready.get("recommended_next_action", ""),
        "summary": crm_ready.get("summary", ai_outputs.get("summary", "")),
        "follow_up_message": crm_ready.get(
            "follow_up_message",
            ai_outputs.get("follow_up_message", ""),
        ),
        "source": crm_ready.get("source", lead.get("source", "")),
        "preferred_contact_method": crm_ready.get("preferred_contact_method", ""),
        "workflow_version": ai_metadata.get("workflow_version", ""),
        "model": ai_metadata.get("model", ""),
    }

    return {column: row.get(column, "") for column in GOOGLE_SHEETS_COLUMNS}


def build_google_sheets_values(result: dict[str, Any]) -> list[Any]:
    """Build one ordered values list ready for spreadsheets.values.append."""
    row = build_google_sheets_row(result)
    return [row[column] for column in GOOGLE_SHEETS_COLUMNS]


def build_google_sheets_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Build a Google Sheets API compatible append payload preview."""
    return {
        "range": GOOGLE_SHEETS_RANGE,
        "majorDimension": "ROWS",
        "columns": GOOGLE_SHEETS_COLUMNS,
        "values": [build_google_sheets_values(result)],
    }


def append_result_to_google_sheet(result: dict[str, Any]) -> dict[str, Any]:
    """Append one processed lead result to the configured live Google Sheet."""
    return append_values_to_google_sheet(values=build_google_sheets_values(result))


def append_values_to_google_sheet(values: list[Any]) -> dict[str, Any]:
    """Append one ordered row of values to the configured live Google Sheet."""
    ensure_google_sheets_configured()
    access_token = get_google_sheets_access_token()
    payload = {
        "range": GOOGLE_SHEETS_RANGE,
        "majorDimension": "ROWS",
        "values": [values],
    }
    response_payload = post_google_sheets_append_request(
        access_token=access_token,
        payload=payload,
    )
    updates = response_payload.get("updates", {})

    return {
        "status": "appended",
        "spreadsheet_id": response_payload.get(
            "spreadsheetId",
            GOOGLE_SHEETS_SPREADSHEET_ID,
        ),
        "range": GOOGLE_SHEETS_RANGE,
        "table_range": response_payload.get("tableRange", ""),
        "updated_range": updates.get("updatedRange", ""),
        "updated_rows": updates.get("updatedRows", 0),
        "updated_columns": updates.get("updatedColumns", 0),
        "updated_cells": updates.get("updatedCells", 0),
        "columns": GOOGLE_SHEETS_COLUMNS,
    }


def ensure_google_sheets_configured() -> None:
    """Raise a clear error if live Google Sheets export is not configured."""
    if not GOOGLE_SHEETS_ENABLED:
        raise GoogleSheetsConfigError(
            "Google Sheets integration is disabled. Set GOOGLE_SHEETS_ENABLED=true."
        )

    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        raise GoogleSheetsConfigError("GOOGLE_SHEETS_SPREADSHEET_ID is missing.")

    if not GOOGLE_SERVICE_ACCOUNT_FILE and not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise GoogleSheetsConfigError(
            "Google service account credentials are missing. Set "
            "GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON."
        )


def get_google_sheets_access_token() -> str:
    """Return a Google API access token using service account credentials."""
    try:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2 import service_account
    except ImportError as error:
        raise GoogleSheetsConfigError(
            "google-auth is not installed. Run: pip install -r requirements.txt"
        ) from error

    if GOOGLE_SERVICE_ACCOUNT_JSON:
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=GOOGLE_SHEETS_SCOPES,
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=GOOGLE_SHEETS_SCOPES,
        )

    credentials.refresh(GoogleAuthRequest())
    return credentials.token


def post_google_sheets_append_request(
    access_token: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """POST one append request to the Google Sheets API."""
    encoded_range = quote(GOOGLE_SHEETS_RANGE, safe="")
    query_string = urlencode(
        {
            "valueInputOption": GOOGLE_SHEETS_VALUE_INPUT_OPTION,
            "insertDataOption": GOOGLE_SHEETS_INSERT_DATA_OPTION,
        }
    )
    url = (
        f"{GOOGLE_SHEETS_API_BASE_URL}/{GOOGLE_SHEETS_SPREADSHEET_ID}"
        f"/values/{encoded_range}:append?{query_string}"
    )
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise GoogleSheetsAppendError(
            f"Google Sheets append request failed: {error}"
        ) from error


def get_ai_metadata(result: dict[str, Any]) -> dict[str, Any]:
    """Return AI metadata from current or legacy output shapes."""
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
