"""Application configuration."""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")


def require_openai_api_key() -> str:
    """Return the OpenAI API key or raise a helpful error."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to a local .env file before "
            "running AI-powered milestones."
        )

    return OPENAI_API_KEY
