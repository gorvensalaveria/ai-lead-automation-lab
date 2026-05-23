"""Save automation outputs locally."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def save_output(result: dict[str, Any], output_dir: str | Path = "data/outputs") -> Path:
    """Save one automation result as a JSON file and return the file path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    lead_id = result["lead"]["lead_id"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = output_path / f"{lead_id}_{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return file_path


def build_result(
    lead: dict[str, Any],
    summary: str,
    classification: str,
    score: dict[str, Any],
    follow_up_message: str,
) -> dict[str, Any]:
    """Build the final automation result that will be saved locally."""
    processed_at = datetime.now(timezone.utc).isoformat()

    return {
        "processed_at": processed_at,
        "lead": lead,
        "ai_outputs": {
            "summary": summary,
            "classification": classification,
            "score": score,
            "follow_up_message": follow_up_message,
        },
        "crm_ready": build_crm_ready_output(
            lead=lead,
            summary=summary,
            classification=classification,
            score=score,
            follow_up_message=follow_up_message,
            processed_at=processed_at,
        ),
    }


def build_crm_ready_output(
    lead: dict[str, Any],
    summary: str,
    classification: str,
    score: dict[str, Any],
    follow_up_message: str,
    processed_at: str,
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
    }


def get_recommended_next_action(classification: str) -> str:
    """Map lead classification to a practical sales follow-up action."""
    normalized_classification = classification.lower()

    if normalized_classification == "hot":
        return "Reply quickly and offer a discovery call or demo."

    if normalized_classification == "warm":
        return "Send helpful details and ask a qualifying follow-up question."

    return "Add to nurture list and follow up with educational content."
