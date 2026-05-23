"""Generate personalized follow-up messages with the OpenAI API."""

import json
from typing import Any

from app.config import OPENAI_MODEL, require_openai_api_key


def generate_follow_up_message(
    lead: dict[str, Any],
    summary: str,
    classification: str,
    score: dict[str, Any],
) -> str:
    """Generate a short follow-up message for one qualified lead."""
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
                "You write follow-up messages for inbound business leads. "
                "Write in a professional, helpful, and concise tone. "
                "Do not invent offers, prices, calendar links, or guarantees. "
                "Keep the message practical for a sales or operations team to review "
                "before sending. Write in plain text only. Do not use Markdown, "
                "asterisks, bold formatting, or bullet points. Do not include "
                "signature placeholders such as [Your Name], [Company Name], "
                "[Phone], or [Website]."
            ),
            input=(
                "Draft a personalized follow-up email for this lead. "
                "Start with a plain text subject line formatted like 'Subject: ...'. "
                "Include a greeting using the lead's first name, "
                "a brief acknowledgement of their need, one helpful next step, "
                "and a polite call to action. End cleanly after the call to action "
                "without adding a signature block or placeholder contact details. "
                "Keep it under 180 words.\n\n"
                f"Lead JSON:\n{json.dumps(lead, indent=2)}\n\n"
                f"Lead summary:\n{summary}\n\n"
                f"Lead classification:\n{classification}\n\n"
                f"Lead score:\n{json.dumps(score, indent=2)}"
            ),
        )
    except OpenAIError as error:
        raise RuntimeError(f"OpenAI follow-up message request failed: {error}") from error

    return response.output_text.strip()
