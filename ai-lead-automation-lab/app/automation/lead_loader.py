"""Load and validate local lead JSON files."""

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_FIELDS = [
    "lead_id",
    "source",
    "submitted_at",
    "business_type",
    "contact",
    "lead_details",
]

REQUIRED_CONTACT_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "company",
]

REQUIRED_LEAD_DETAIL_FIELDS = [
    "service_interest",
    "message",
    "budget_range",
    "timeline",
    "preferred_contact_method",
]


def load_lead(file_path: str | Path) -> dict[str, Any]:
    """Load one lead from a JSON file and validate its required fields."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Lead file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        lead = json.load(file)

    validate_lead(lead)
    return lead


def validate_lead(lead: dict[str, Any]) -> None:
    """Validate that a lead has the required structure."""
    if not isinstance(lead, dict):
        raise ValueError("Lead data must be a JSON object.")

    missing_top_level = find_missing_fields(lead, REQUIRED_TOP_LEVEL_FIELDS)
    if missing_top_level:
        raise ValueError(
            "Lead is missing required top-level fields: "
            + ", ".join(missing_top_level)
        )

    contact = lead["contact"]
    if not isinstance(contact, dict):
        raise ValueError("Lead contact must be a JSON object.")

    missing_contact = find_missing_fields(contact, REQUIRED_CONTACT_FIELDS)
    if missing_contact:
        raise ValueError(
            "Lead contact is missing required fields: "
            + ", ".join(missing_contact)
        )

    lead_details = lead["lead_details"]
    if not isinstance(lead_details, dict):
        raise ValueError("Lead details must be a JSON object.")

    missing_lead_details = find_missing_fields(
        lead_details,
        REQUIRED_LEAD_DETAIL_FIELDS,
    )
    if missing_lead_details:
        raise ValueError(
            "Lead details are missing required fields: "
            + ", ".join(missing_lead_details)
        )


def find_missing_fields(data: dict[str, Any], required_fields: list[str]) -> list[str]:
    """Return required fields that are missing or blank."""
    missing_fields = []

    for field in required_fields:
        value = data.get(field)
        if value is None or value == "":
            missing_fields.append(field)

    return missing_fields
