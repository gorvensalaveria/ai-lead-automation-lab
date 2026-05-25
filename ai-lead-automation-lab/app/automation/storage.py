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


def list_saved_outputs(output_dir: str | Path = "data/outputs") -> list[dict[str, Any]]:
    """Return saved automation outputs as compact history rows."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return []

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
