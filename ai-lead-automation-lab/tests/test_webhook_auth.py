import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation.storage import build_result


client = TestClient(app)


def setup_function():
    api_module.GOOGLE_SHEETS_AUTO_APPEND = False


def valid_lead_payload() -> dict:
    return {
        "lead_id": "lead_valid",
        "source": "website_form",
        "submitted_at": "2026-05-25T10:00:00+00:00",
        "business_type": "saas",
        "contact": {
            "first_name": "Ana",
            "last_name": "Santos",
            "email": "ana@example.com",
            "phone": "+63 917 555 0123",
            "company": "Santos Software",
        },
        "lead_details": {
            "service_interest": "lead automation",
            "message": "We need help qualifying inbound leads.",
            "budget_range": "USD 2,000 - USD 5,000",
            "timeline": "urgent",
            "preferred_contact_method": "email",
        },
    }


def sample_processed_result() -> dict:
    return build_result(
        lead=valid_lead_payload(),
        summary="Ana wants lead automation.",
        classification="hot",
        score={
            "total_score": 100,
            "max_score": 100,
            "rating": "high",
            "breakdown": {
                "fit": 25,
                "urgency": 25,
                "budget": 25,
                "intent": 25,
            },
        },
        follow_up_message="Hi Ana, thanks for reaching out.",
    )


def process_without_openai(lead):
    return sample_processed_result(), "data/outputs/lead_valid.json"


def signed_headers(body: bytes, timestamp: str = "200") -> dict[str, str]:
    digest = hmac.new(
        b"test-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": f"sha256={digest}",
    }


def test_auth_disabled_preserves_webhook_behavior(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "process_lead", process_without_openai)

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Forwarded-For": "auth-disabled-client"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_webhook_auth_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_API_KEYS", ["local-dev-key"])
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)

    response = client.post("/webhooks/leads", json=valid_lead_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key."}


def test_webhook_auth_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_API_KEYS", ["local-dev-key"])
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key."}


def test_webhook_auth_accepts_valid_api_key(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_API_KEYS", ["local-dev-key"])
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "process_lead", process_without_openai)

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={
            "X-API-Key": "local-dev-key",
            "X-Forwarded-For": "valid-api-key-client",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_hmac_rejects_missing_signature(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={"Content-Type": "application/json", "X-Webhook-Timestamp": "200"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}


def test_hmac_rejects_malformed_signature(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": "200",
            "X-Webhook-Signature": "not-a-sha256-signature",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}


def test_hmac_rejects_invalid_signature(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": "200",
            "X-Webhook-Signature": "sha256=bad",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}


def test_hmac_rejects_malformed_timestamp(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": "not-a-timestamp",
            "X-Webhook-Signature": "sha256=bad",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}


def test_hmac_rejects_expired_timestamp(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")
    monkeypatch.setattr(api_module, "WEBHOOK_SIGNATURE_TOLERANCE_SECONDS", 1)

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={
            "Content-Type": "application/json",
            **signed_headers(body, timestamp="1"),
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}


def test_hmac_accepts_valid_signature(monkeypatch):
    body = json.dumps(valid_lead_payload()).encode("utf-8")
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "test-secret")
    monkeypatch.setattr(api_module, "WEBHOOK_REPLAY_PROTECTION_ENABLED", False)
    monkeypatch.setattr(api_module, "process_lead", process_without_openai)

    response = client.post(
        "/webhooks/leads",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": "valid-hmac-client",
            **signed_headers(body),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_hmac_enabled_without_secret_returns_server_config_error(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", True)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_SECRET", "")

    response = client.post("/webhooks/leads", json=valid_lead_payload())

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Webhook HMAC is enabled but not configured.",
    }


def test_invalid_json_returns_required_error(monkeypatch):
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)

    response = client.post(
        "/webhooks/leads",
        content=b"{bad-json",
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": "invalid-json-client",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid JSON payload."}
