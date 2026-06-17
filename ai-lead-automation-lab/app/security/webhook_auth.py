"""Authentication and signature verification for inbound webhooks."""

import hashlib
import hmac
import time
from collections.abc import Callable, Sequence


API_KEY_ERROR_DETAIL = "Missing or invalid API key."
HMAC_ERROR_DETAIL = "Invalid webhook signature."
HMAC_NOT_CONFIGURED_DETAIL = "Webhook HMAC is enabled but not configured."


def is_valid_api_key(provided_key: str | None, allowed_keys: Sequence[str]) -> bool:
    """Return whether the provided API key matches one configured key."""
    if not provided_key:
        return False

    normalized_key = provided_key.strip()
    if not normalized_key:
        return False

    return any(
        hmac.compare_digest(normalized_key, allowed_key)
        for allowed_key in allowed_keys
        if allowed_key
    )


def is_valid_hmac_signature(
    *,
    raw_body: bytes,
    timestamp: str | None,
    signature: str | None,
    secret: str,
    tolerance_seconds: int,
    replay_protection_enabled: bool = True,
    now: Callable[[], float] = time.time,
) -> bool:
    """Return whether a webhook HMAC signature is valid for the raw body."""
    if not timestamp or not signature or not secret:
        return False

    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False

    if replay_protection_enabled:
        age_seconds = abs(now() - timestamp_value)
        if age_seconds > max(0, tolerance_seconds):
            return False

    if not signature.startswith("sha256="):
        return False

    provided_digest = signature.removeprefix("sha256=").strip()
    if not provided_digest:
        return False

    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected_digest = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(provided_digest, expected_digest)
