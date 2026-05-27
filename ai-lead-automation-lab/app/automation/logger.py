"""Logging setup for the local automation workflow."""

import json
import logging
from pathlib import Path
from typing import Any


LOG_FILE = Path("logs/app.log")


def setup_logger(name: str = "ai_lead_automation") -> logging.Logger:
    """Create a logger that writes to a local log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def log_structured_event(
    logger: logging.Logger,
    event: str,
    **fields: Any,
) -> None:
    """Write one structured JSON event to the application log."""
    payload = {
        "event": event,
        **fields,
    }
    logger.info(json.dumps(payload, default=str, sort_keys=True))
