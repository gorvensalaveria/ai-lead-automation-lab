"""Airtable destination handler for processed lead records."""

from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from app.config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_ENABLED,
    AIRTABLE_TABLE_NAME,
    AIRTABLE_TIMEOUT_SECONDS,
)


AIRTABLE_API_BASE_URL = "https://api.airtable.com/v0"
AIRTABLE_NOT_CONFIGURED_MESSAGE = "Airtable integration is enabled but not configured."


class AirtableConfigError(RuntimeError):
    """Raised when Airtable delivery is enabled without required config."""


class AirtableDeliveryError(RuntimeError):
    """Raised when Airtable delivery fails."""


def send_processed_lead_to_airtable(
    processed_lead: dict[str, Any],
    output_path: str | None = None,
    *,
    enabled: bool = AIRTABLE_ENABLED,
    api_key: str = AIRTABLE_API_KEY,
    base_id: str = AIRTABLE_BASE_ID,
    table_name: str = AIRTABLE_TABLE_NAME,
    timeout_seconds: float = AIRTABLE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Send one processed lead record to Airtable."""
    ensure_airtable_configured(
        enabled=enabled,
        api_key=api_key,
        base_id=base_id,
        table_name=table_name,
    )
    payload = build_airtable_payload(processed_lead, output_path=output_path)
    response_payload = post_airtable_record(
        payload=payload,
        api_key=api_key,
        base_id=base_id,
        table_name=table_name,
        timeout_seconds=timeout_seconds,
    )
    records = response_payload.get("records", [])
    first_record = records[0] if records else {}

    return {
        "status": "sent",
        "record_id": first_record.get("id", ""),
    }


def ensure_airtable_configured(
    *,
    enabled: bool,
    api_key: str,
    base_id: str,
    table_name: str,
) -> None:
    """Raise a safe error when Airtable is enabled without required config."""
    if not enabled:
        raise AirtableConfigError("Airtable integration is disabled.")

    if not api_key or not base_id or not table_name:
        raise AirtableConfigError(AIRTABLE_NOT_CONFIGURED_MESSAGE)


def build_airtable_payload(
    processed_lead: dict[str, Any],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Build one Airtable create-record payload for a processed lead."""
    return {
        "records": [
            {
                "fields": build_airtable_fields(
                    processed_lead,
                    output_path=output_path,
                ),
            },
        ],
    }


def build_airtable_fields(
    processed_lead: dict[str, Any],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Map processed lead data to simple Airtable fields."""
    lead = processed_lead.get("lead", {})
    contact = lead.get("contact", {})
    ai_outputs = processed_lead.get("ai_outputs", {})
    crm_ready = processed_lead.get("crm_ready", {})
    output_file = Path(output_path).name if output_path else ""

    fields = {
        "Lead ID": crm_ready.get("lead_id", lead.get("lead_id", "")),
        "Name": crm_ready.get("contact_name", ""),
        "Email": crm_ready.get("email", contact.get("email", "")),
        "Phone": crm_ready.get("phone", contact.get("phone", "")),
        "Company": crm_ready.get("company", contact.get("company", "")),
        "Source": crm_ready.get("source", lead.get("source", "")),
        "Status": crm_ready.get("review_status", processed_lead.get("review_status", "new")),
        "Score": crm_ready.get("lead_score", ""),
        "Notes": crm_ready.get("summary", ai_outputs.get("summary", "")),
        "Output File": output_file,
        "Created At": crm_ready.get("processed_at", processed_lead.get("processed_at", "")),
    }

    return {
        field_name: value
        for field_name, value in fields.items()
        if value is not None
    }


def post_airtable_record(
    *,
    payload: dict[str, Any],
    api_key: str,
    base_id: str,
    table_name: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Create one Airtable record through the Airtable REST API."""
    url = build_airtable_records_url(base_id=base_id, table_name=table_name)
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise AirtableDeliveryError("Airtable delivery failed.") from error


def build_airtable_records_url(base_id: str, table_name: str) -> str:
    """Return the Airtable records endpoint for one base and table."""
    encoded_table_name = quote(table_name, safe="")
    return f"{AIRTABLE_API_BASE_URL}/{base_id}/{encoded_table_name}"
