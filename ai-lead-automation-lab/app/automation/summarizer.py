"""Summarize lead details with the OpenAI API."""

import json
from typing import Any

from app.automation.openai_client import create_openai_response
from app.config import OPENAI_MODEL


def summarize_lead(lead: dict[str, Any]) -> str:
    """Generate a short business summary for one lead."""
    response = create_openai_response(
        operation="summary",
        model=OPENAI_MODEL,
        instructions=(
            "You summarize inbound business leads for an AI automation specialist. "
            "Write clearly and professionally. Do not invent details. "
            "Keep the summary useful for a sales or operations team. "
            "Write in plain text only. Do not use Markdown, asterisks, "
            "bold formatting, headings, or bullet points. Write only in English. "
            "Do not use non-English words, translations, or non-Latin characters. "
            "If a detail is missing or unclear, describe it in English as "
            "'not provided', 'not finalized', or 'not sure'."
        ),
        input=(
            "Summarize this lead in 1-2 concise sentences. Focus on the business "
            "need, service interest, budget clarity, timeline, and relevant tools "
            "or workflow context. Do not repeat every field, and do not include "
            "the phone number unless it is important to the need. Use only "
            "English words and standard punctuation.\n\n"
            f"Lead JSON:\n{json.dumps(lead, indent=2)}"
        ),
    )

    return response.output_text.strip()
