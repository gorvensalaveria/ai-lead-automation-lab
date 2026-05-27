"""Google Sheets handoff payload builder."""

from typing import Any


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
        "range": "Leads!A:T",
        "majorDimension": "ROWS",
        "columns": GOOGLE_SHEETS_COLUMNS,
        "values": [build_google_sheets_values(result)],
    }


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
