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
    return {
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "lead": lead,
        "ai_outputs": {
            "summary": summary,
            "classification": classification,
            "score": score,
            "follow_up_message": follow_up_message,
        },
    }
