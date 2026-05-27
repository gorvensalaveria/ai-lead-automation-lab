"""OpenAI client helpers with controlled retry and backoff behavior."""

import random
import time
from collections.abc import Callable
from typing import Any

from app.automation.logger import log_structured_event, setup_logger
from app.config import (
    OPENAI_MAX_RETRIES,
    OPENAI_RETRY_BASE_SECONDS,
    OPENAI_TIMEOUT_SECONDS,
    require_openai_api_key,
)


TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
TRANSIENT_ERROR_NAMES = {
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError",
    "RateLimitError",
}

logger = setup_logger()


def get_openai_client() -> Any:
    """Return an OpenAI client configured for app-controlled retries."""
    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError(
            "The openai package is not installed. Run: pip install -r requirements.txt"
        ) from error

    return OpenAI(
        api_key=require_openai_api_key(),
        max_retries=0,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )


def create_openai_response(
    *,
    operation: str,
    model: str,
    instructions: str,
    input: str,
) -> Any:
    """Create one OpenAI Responses API result with retry/backoff handling."""
    client = get_openai_client()

    return retry_openai_operation(
        operation=operation,
        request_callable=lambda: client.responses.create(
            model=model,
            instructions=instructions,
            input=input,
        ),
    )


def retry_openai_operation(
    *,
    operation: str,
    request_callable: Callable[[], Any],
    max_retries: int = OPENAI_MAX_RETRIES,
    base_delay_seconds: float = OPENAI_RETRY_BASE_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
    jitter: Callable[[float, float], float] = random.uniform,
) -> Any:
    """Retry transient OpenAI errors with exponential backoff and jitter."""
    attempt = 0

    while True:
        try:
            response = request_callable()
            if attempt:
                log_structured_event(
                    logger,
                    event="openai_retry_succeeded",
                    operation=operation,
                    attempt=attempt,
                )
            return response
        except Exception as error:
            if not is_transient_openai_error(error) or attempt >= max_retries:
                log_structured_event(
                    logger,
                    event="openai_request_failed",
                    operation=operation,
                    attempt=attempt,
                    max_retries=max_retries,
                    error_type=type(error).__name__,
                    error=str(error),
                    retryable=is_transient_openai_error(error),
                )
                raise RuntimeError(f"OpenAI {operation} request failed: {error}") from error

            attempt += 1
            delay_seconds = calculate_retry_delay(
                attempt=attempt,
                base_delay_seconds=base_delay_seconds,
                jitter=jitter,
            )
            log_structured_event(
                logger,
                event="openai_retry_scheduled",
                operation=operation,
                attempt=attempt,
                max_retries=max_retries,
                delay_seconds=round(delay_seconds, 3),
                error_type=type(error).__name__,
                error=str(error),
            )
            sleeper(delay_seconds)


def is_transient_openai_error(error: Exception) -> bool:
    """Return whether an OpenAI-style error should be retried."""
    status_code = getattr(error, "status_code", None)
    if status_code in TRANSIENT_STATUS_CODES:
        return True

    return type(error).__name__ in TRANSIENT_ERROR_NAMES


def calculate_retry_delay(
    *,
    attempt: int,
    base_delay_seconds: float,
    jitter: Callable[[float, float], float] = random.uniform,
) -> float:
    """Return exponential backoff delay with a small jitter."""
    exponential_delay = base_delay_seconds * (2 ** (attempt - 1))
    return exponential_delay + jitter(0, base_delay_seconds)
