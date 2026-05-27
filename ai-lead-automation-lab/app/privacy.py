"""Privacy helpers for masking lead contact data."""

import copy
from typing import Any


def is_masked_mode(value: str | bool | None) -> bool:
    """Return whether a request should render masked contact data."""
    if isinstance(value, bool):
        return value

    return str(value or "").strip().lower() in {"1", "true", "yes", "masked"}


def mask_email(email: Any) -> str:
    """Mask an email address while keeping it recognizable for review."""
    raw_email = str(email or "").strip()
    if "@" not in raw_email:
        return raw_email

    local_part, domain = raw_email.split("@", 1)
    if not local_part:
        return f"***@{domain}"

    visible_prefix = local_part[: min(3, len(local_part))]
    return f"{visible_prefix}{'*' * 5}@{domain}"


def mask_phone(phone: Any) -> str:
    """Mask a phone number while preserving country code and last digits."""
    raw_phone = str(phone or "").strip()
    digits = [character for character in raw_phone if character.isdigit()]
    if len(digits) <= 4:
        return raw_phone

    last_digits = "".join(digits[-4:])
    prefix = ""
    if raw_phone.startswith("+") and digits:
        prefix = f"+{digits[0]} "

    return f"{prefix}*** *** {last_digits}"


def mask_lead_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a saved lead result with direct contact fields masked."""
    masked_result = copy.deepcopy(result)
    contact = masked_result.get("lead", {}).get("contact", {})
    crm_ready = masked_result.get("crm_ready", {})

    if "email" in contact:
        contact["email"] = mask_email(contact["email"])
    if "phone" in contact:
        contact["phone"] = mask_phone(contact["phone"])

    if "email" in crm_ready:
        crm_ready["email"] = mask_email(crm_ready["email"])
    if "phone" in crm_ready:
        crm_ready["phone"] = mask_phone(crm_ready["phone"])

    return masked_result
