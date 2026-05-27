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
APP_ENV = os.getenv("APP_ENV", "development")
WORKFLOW_VERSION = os.getenv("WORKFLOW_VERSION", "lead-intake-v1")
SUMMARY_PROMPT_VERSION = os.getenv("SUMMARY_PROMPT_VERSION", "summary-v1")
CLASSIFICATION_PROMPT_VERSION = os.getenv(
    "CLASSIFICATION_PROMPT_VERSION",
    "classification-v1",
)
FOLLOW_UP_PROMPT_VERSION = os.getenv("FOLLOW_UP_PROMPT_VERSION", "follow-up-v1")
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_RETRY_BASE_SECONDS = float(os.getenv("OPENAI_RETRY_BASE_SECONDS", "1"))
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
LEAD_PROCESS_RATE_LIMIT_PER_MINUTE = int(
    os.getenv("LEAD_PROCESS_RATE_LIMIT_PER_MINUTE", "3")
)
LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS", "60")
)


def require_openai_api_key() -> str:
    """Return the OpenAI API key or raise a helpful error."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to a local .env file before "
            "running AI-powered milestones."
        )

    return OPENAI_API_KEY
