"""HubSpot CRM destination handler for processed lead contacts."""

from typing import Any

import requests

from app.config import (
    HUBSPOT_ACCESS_TOKEN,
    HUBSPOT_ENABLED,
    HUBSPOT_TIMEOUT_SECONDS,
)


HUBSPOT_CONTACTS_API_URL = "https://api.hubapi.com/crm/v3/objects/contacts"
HUBSPOT_NOT_CONFIGURED_MESSAGE = "HubSpot integration is enabled but not configured."
HUBSPOT_DELIVERY_FAILED_MESSAGE = "HubSpot delivery failed."


class HubSpotConfigError(RuntimeError):
    """Raised when HubSpot delivery is enabled without required config."""


class HubSpotDeliveryError(RuntimeError):
    """Raised when HubSpot contact delivery fails."""


def send_processed_lead_to_hubspot(
    processed_lead: dict[str, Any],
    *,
    enabled: bool = HUBSPOT_ENABLED,
    access_token: str = HUBSPOT_ACCESS_TOKEN,
    timeout_seconds: float = HUBSPOT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Send one processed lead to HubSpot as a contact create request."""
    ensure_hubspot_configured(enabled=enabled, access_token=access_token)
    response_payload = post_hubspot_contact(
        payload=build_hubspot_payload(processed_lead),
        access_token=access_token,
        timeout_seconds=timeout_seconds,
    )

    return {
        "status": "sent",
        "object_id": response_payload.get("id", ""),
    }


def ensure_hubspot_configured(*, enabled: bool, access_token: str) -> None:
    """Raise a safe error when HubSpot is enabled without required config."""
    if not enabled:
        raise HubSpotConfigError("HubSpot integration is disabled.")

    if not access_token:
        raise HubSpotConfigError(HUBSPOT_NOT_CONFIGURED_MESSAGE)


def build_hubspot_payload(processed_lead: dict[str, Any]) -> dict[str, Any]:
    """Build a HubSpot CRM v3 contact create payload."""
    return {"properties": build_hubspot_properties(processed_lead)}


def build_hubspot_properties(processed_lead: dict[str, Any]) -> dict[str, str]:
    """Map processed lead data to simple HubSpot contact properties."""
    lead = processed_lead.get("lead", {})
    contact = lead.get("contact", {})
    lead_details = lead.get("lead_details", {})
    ai_outputs = processed_lead.get("ai_outputs", {})
    crm_ready = processed_lead.get("crm_ready", {})
    score = ai_outputs.get("score", {})
    first_name, last_name = split_contact_name(
        crm_ready.get("contact_name")
        or contact.get("name")
        or lead.get("name")
        or ""
    )

    properties = {
        "email": crm_ready.get("email", contact.get("email", "")),
        "firstname": first_name,
        "lastname": last_name,
        "phone": crm_ready.get("phone", contact.get("phone", "")),
        "company": crm_ready.get("company", contact.get("company", "")),
        "lifecyclestage": "lead",
        "hs_lead_status": "NEW",
        "ai_lead_score": stringify_property(
            crm_ready.get("lead_score", score.get("total_score", ""))
        ),
        "ai_classification": stringify_property(
            crm_ready.get("classification", ai_outputs.get("classification", ""))
        ),
        "ai_summary": stringify_property(
            crm_ready.get("summary", ai_outputs.get("summary", ""))
        ),
        "ai_follow_up": stringify_property(
            crm_ready.get("follow_up_message", ai_outputs.get("follow_up_message", ""))
        ),
        "lead_source": stringify_property(
            crm_ready.get("source", lead.get("source", ""))
        ),
        "lead_budget": stringify_property(lead_details.get("budget_range", "")),
        "lead_timeline": stringify_property(lead_details.get("timeline", "")),
    }

    return {
        property_name: property_value
        for property_name, property_value in properties.items()
        if property_value is not None
    }


def split_contact_name(contact_name: str) -> tuple[str | None, str | None]:
    """Split a contact name into HubSpot firstname and lastname values."""
    name_parts = str(contact_name or "").strip().split()
    if not name_parts:
        return None, None

    if len(name_parts) == 1:
        return name_parts[0], None

    return name_parts[0], " ".join(name_parts[1:])


def stringify_property(value: Any) -> str | None:
    """Return a simple string property value for HubSpot."""
    if value is None:
        return None

    return str(value)


def post_hubspot_contact(
    *,
    payload: dict[str, Any],
    access_token: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Create one HubSpot contact through the CRM v3 API."""
    try:
        response = requests.post(
            HUBSPOT_CONTACTS_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise HubSpotDeliveryError(HUBSPOT_DELIVERY_FAILED_MESSAGE) from error
