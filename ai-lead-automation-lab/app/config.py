"""Application configuration."""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


def get_bool_env(name: str, default: bool = False) -> bool:
    """Return a boolean environment flag."""
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


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
WEBHOOK_AUTH_ENABLED = get_bool_env("WEBHOOK_AUTH_ENABLED", False)
WEBHOOK_API_KEYS = [
    key.strip()
    for key in os.getenv("WEBHOOK_API_KEYS", "local-dev-key").split(",")
    if key.strip()
]
WEBHOOK_HMAC_ENABLED = get_bool_env("WEBHOOK_HMAC_ENABLED", False)
WEBHOOK_HMAC_SECRET = os.getenv("WEBHOOK_HMAC_SECRET", "")
WEBHOOK_SIGNATURE_TOLERANCE_SECONDS = int(
    os.getenv("WEBHOOK_SIGNATURE_TOLERANCE_SECONDS", "300")
)
WEBHOOK_REPLAY_PROTECTION_ENABLED = get_bool_env(
    "WEBHOOK_REPLAY_PROTECTION_ENABLED",
    True,
)
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
GOOGLE_SHEETS_AUTO_APPEND = (
    os.getenv("GOOGLE_SHEETS_AUTO_APPEND", "false").lower() == "true"
)
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SHEETS_RANGE = os.getenv("GOOGLE_SHEETS_RANGE", "Leads!A:T")
GOOGLE_SHEETS_VALUE_INPUT_OPTION = os.getenv(
    "GOOGLE_SHEETS_VALUE_INPUT_OPTION",
    "RAW",
)
GOOGLE_SHEETS_INSERT_DATA_OPTION = os.getenv(
    "GOOGLE_SHEETS_INSERT_DATA_OPTION",
    "INSERT_ROWS",
)
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
AIRTABLE_ENABLED = get_bool_env("AIRTABLE_ENABLED", False)
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "")
AIRTABLE_TIMEOUT_SECONDS = float(os.getenv("AIRTABLE_TIMEOUT_SECONDS", "10"))
HUBSPOT_ENABLED = get_bool_env("HUBSPOT_ENABLED", False)
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
HUBSPOT_TIMEOUT_SECONDS = float(os.getenv("HUBSPOT_TIMEOUT_SECONDS", "10"))


def require_openai_api_key() -> str:
    """Return the OpenAI API key or raise a helpful error."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to a local .env file before "
            "running AI-powered milestones."
        )

    return OPENAI_API_KEY
