import json
import re
from pathlib import Path


MAKE_DIR = Path("integrations/make")
ZAPIER_DIR = Path("integrations/zapier")

MAKE_README = MAKE_DIR / "README.md"
MAKE_BLUEPRINT = MAKE_DIR / "lead-intake-ai-automation.blueprint.json"
MAKE_PAYLOAD = MAKE_DIR / "sample-webhook-payload.json"
MAKE_HEADERS = MAKE_DIR / "sample-secure-headers.md"

ZAPIER_README = ZAPIER_DIR / "README.md"
ZAPIER_SETUP = ZAPIER_DIR / "ZAPIER_SETUP.md"
ZAPIER_PAYLOAD = ZAPIER_DIR / "sample-webhook-payload.json"
ZAPIER_HEADERS = ZAPIER_DIR / "sample-secure-headers.md"


def test_make_assets_exist():
    assert MAKE_README.exists()
    assert MAKE_BLUEPRINT.exists()
    assert MAKE_PAYLOAD.exists()
    assert MAKE_HEADERS.exists()


def test_make_blueprint_is_valid_json_and_references_webhook_headers():
    blueprint = json.loads(MAKE_BLUEPRINT.read_text(encoding="utf-8"))
    blueprint_text = MAKE_BLUEPRINT.read_text(encoding="utf-8")

    assert blueprint["name"]
    assert blueprint["blueprint_type"] == "documented_starter_pseudo_blueprint"
    assert "/webhooks/leads" in blueprint_text
    assert "X-API-Key" in blueprint_text
    assert "Idempotency-Key" in blueprint_text


def test_make_sample_payload_has_required_fields():
    payload = json.loads(MAKE_PAYLOAD.read_text(encoding="utf-8"))

    assert payload["name"]
    assert payload["email"]
    assert payload["company"]
    assert payload["source"]
    assert payload.get("message") or payload.get("pain_point")


def test_zapier_assets_exist():
    assert ZAPIER_README.exists()
    assert ZAPIER_SETUP.exists()
    assert ZAPIER_PAYLOAD.exists()
    assert ZAPIER_HEADERS.exists()


def test_zapier_docs_reference_webhook_and_security_headers():
    docs_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ZAPIER_README, ZAPIER_SETUP, ZAPIER_HEADERS]
    )

    assert "/webhooks/leads" in docs_text
    assert "X-API-Key" in docs_text
    assert "Idempotency-Key" in docs_text


def test_zapier_sample_payload_has_required_fields():
    payload = json.loads(ZAPIER_PAYLOAD.read_text(encoding="utf-8"))

    assert payload["name"]
    assert payload["email"]
    assert payload["company"]
    assert payload["source"]
    assert payload.get("message") or payload.get("pain_point")


def test_make_and_zapier_docs_explain_fastapi_owns_downstream_dispatch():
    docs_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            MAKE_README,
            MAKE_BLUEPRINT,
            ZAPIER_README,
            ZAPIER_SETUP,
        ]
    )

    assert "FastAPI processes the lead with AI" in docs_text
    assert "integration dispatcher" in docs_text
    assert "FastAPI handles downstream Google Sheets, Airtable, and HubSpot dispatch" in docs_text


def test_make_and_zapier_docs_do_not_claim_direct_downstream_writes():
    docs_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [MAKE_README, ZAPIER_README, ZAPIER_SETUP]
    )

    forbidden_claims = [
        "Make writes to Google Sheets",
        "Make writes to Airtable",
        "Make writes to HubSpot",
        "Zapier writes to Google Sheets",
        "Zapier writes to Airtable",
        "Zapier writes to HubSpot",
        "directly write to Airtable, HubSpot, or Google Sheets",
    ]

    assert "Make should not directly write to Airtable, HubSpot, or Google Sheets" in docs_text
    assert "Zapier should not directly write to Airtable, HubSpot, or Google Sheets" in docs_text
    for forbidden_claim in forbidden_claims[:6]:
        assert forbidden_claim not in docs_text


def test_make_and_zapier_secure_headers_document_hmac_format():
    headers_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [MAKE_HEADERS, ZAPIER_HEADERS]
    )

    assert "X-Webhook-Timestamp" in headers_text
    assert "X-Webhook-Signature" in headers_text
    assert '"{timestamp}.{raw_body}"' in headers_text
    assert "sha256=<hex_digest>" in headers_text
    assert "disabled by default locally" in headers_text


def test_make_and_zapier_assets_do_not_contain_obvious_real_secrets():
    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            MAKE_README,
            MAKE_BLUEPRINT,
            MAKE_PAYLOAD,
            MAKE_HEADERS,
            ZAPIER_README,
            ZAPIER_SETUP,
            ZAPIER_PAYLOAD,
            ZAPIER_HEADERS,
        ]
    )
    obvious_secret_patterns = [
        r"sk-[A-Za-z0-9_-]{20,}",
        r"pat[A-Za-z0-9]{20,}",
        r"key[A-Za-z0-9]{20,}",
        r"Bearer\s+[A-Za-z0-9._-]{20,}",
        r"https://[^\\s\"']*(?:ngrok|trycloudflare|localhost\\.run)[^\\s\"']*",
    ]

    for pattern in obvious_secret_patterns:
        assert re.search(pattern, combined_text) is None
