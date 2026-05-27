"""Classify a lead as hot, warm, or cold with the OpenAI API."""

import json
from typing import Any

from app.automation.openai_client import create_openai_response
from app.config import OPENAI_MODEL


VALID_CLASSIFICATIONS = ["hot", "warm", "cold"]


def classify_lead(lead: dict[str, Any]) -> str:
    """Classify one lead as hot, warm, or cold."""
    response = create_openai_response(
        operation="classification",
        model=OPENAI_MODEL,
        instructions=(
            "You classify inbound business leads for a sales or operations team. "
            "Use only one classification: hot, warm, or cold. "
            "Hot means high urgency, strong fit, clear budget, and clear buying intent. "
            "Warm means some fit or interest, but timing, budget, or intent is less clear. "
            "If the lead is exploring, comparing options, or has a budget that is not finalized, "
            "classify it as warm unless there is explicit urgency and strong buying intent. "
            "Cold means low urgency, weak fit, unclear intent, or poor readiness. "
            "Return only the classification word in lowercase English. Do not return "
            "extra text, punctuation, non-English words, or non-Latin characters."
        ),
        input=(
            "Classify this lead as hot, warm, or cold.\n\n"
            f"Lead JSON:\n{json.dumps(lead, indent=2)}"
        ),
    )

    classification = response.output_text.strip().lower()

    if classification not in VALID_CLASSIFICATIONS:
        raise RuntimeError(
            "OpenAI returned an unexpected classification: "
            f"{classification}. Expected hot, warm, or cold."
        )

    return classification
