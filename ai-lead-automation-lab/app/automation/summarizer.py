"""Summarize lead details with the OpenAI API."""

import json
from typing import Any

from app.config import OPENAI_MODEL, require_openai_api_key


def summarize_lead(lead: dict[str, Any]) -> str:
    """Generate a short business summary for one lead."""
    try:
        from openai import OpenAI, OpenAIError
    except ImportError as error:
        raise RuntimeError(
            "The openai package is not installed. Run: pip install -r requirements.txt"
        ) from error

    client = OpenAI(api_key=require_openai_api_key())

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=(
                "You summarize inbound business leads for an AI automation specialist. "
                "Write clearly and professionally. Do not invent details. "
                "Keep the summary useful for a sales or operations team."
            ),
            input=(
                "Summarize this lead in 2-3 sentences. Include the service interest, "
                "business need, budget range, timeline, and preferred contact method "
                "when available.\n\n"
                f"Lead JSON:\n{json.dumps(lead, indent=2)}"
            ),
        )
    except OpenAIError as error:
        raise RuntimeError(f"OpenAI summary request failed: {error}") from error

    return response.output_text.strip()
