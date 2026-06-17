import requests

import app.api as api_module
from app.api import app
from app.automation.storage import build_result
from app.integrations.airtable import (
    AIRTABLE_NOT_CONFIGURED_MESSAGE,
    AirtableConfigError,
    AirtableDeliveryError,
    build_airtable_fields,
    build_airtable_payload,
    build_airtable_records_url,
    send_processed_lead_to_airtable,
)
from fastapi.testclient import TestClient


client = TestClient(app)


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


def test_airtable_payload_maps_processed_lead_fields():
    fields = build_airtable_fields(
        sample_processed_result(),
        output_path="data/outputs/lead_valid_20260616.json",
    )

    assert fields["Lead ID"] == "lead_valid"
    assert fields["Name"] == "Ana Santos"
    assert fields["Email"] == "ana@example.com"
    assert fields["Phone"] == "+63 917 555 0123"
    assert fields["Company"] == "Santos Software"
    assert fields["Source"] == "website_form"
    assert fields["Status"] == "new"
    assert fields["Score"] == 100
    assert fields["Notes"] == "Ana wants lead automation."
    assert fields["Output File"] == "lead_valid_20260616.json"
    assert fields["Created At"]


def test_airtable_payload_uses_records_shape():
    payload = build_airtable_payload(
        sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
    )

    assert list(payload) == ["records"]
    assert len(payload["records"]) == 1
    assert payload["records"][0]["fields"]["Lead ID"] == "lead_valid"


def test_airtable_url_encodes_table_name():
    url = build_airtable_records_url(
        base_id="app123",
        table_name="Qualified Leads",
    )

    assert url == "https://api.airtable.com/v0/app123/Qualified%20Leads"


def test_airtable_enabled_but_missing_config_raises_safe_error():
    try:
        send_processed_lead_to_airtable(
            sample_processed_result(),
            output_path="data/outputs/lead_valid.json",
            enabled=True,
            api_key="",
            base_id="app123",
            table_name="Leads",
        )
    except AirtableConfigError as error:
        assert str(error) == AIRTABLE_NOT_CONFIGURED_MESSAGE
        assert "token" not in str(error).lower()
    else:
        raise AssertionError("Missing Airtable config should raise.")


def test_airtable_enabled_and_configured_sends_one_record(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"records": [{"id": "rec123"}]}

    def fake_post(url, json, headers, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.integrations.airtable.requests.post", fake_post)

    result = send_processed_lead_to_airtable(
        sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        enabled=True,
        api_key="airtable-secret",
        base_id="app123",
        table_name="Qualified Leads",
        timeout_seconds=7,
    )

    assert result == {"status": "sent", "record_id": "rec123"}
    assert calls["url"] == "https://api.airtable.com/v0/app123/Qualified%20Leads"
    assert calls["json"]["records"][0]["fields"]["Lead ID"] == "lead_valid"
    assert calls["headers"]["Authorization"] == "Bearer airtable-secret"
    assert calls["timeout"] == 7


def test_airtable_handler_does_not_expose_secret_in_delivery_errors(monkeypatch):
    def fake_post(url, json, headers, timeout):
        raise requests.RequestException("401 Unauthorized for token airtable-secret")

    monkeypatch.setattr("app.integrations.airtable.requests.post", fake_post)

    try:
        send_processed_lead_to_airtable(
            sample_processed_result(),
            output_path="data/outputs/lead_valid.json",
            enabled=True,
            api_key="airtable-secret",
            base_id="app123",
            table_name="Leads",
        )
    except AirtableDeliveryError as error:
        assert str(error) == "Airtable delivery failed."
        assert "airtable-secret" not in str(error)
        assert "Traceback" not in str(error)
    else:
        raise AssertionError("Airtable request failure should raise.")


def test_webhook_successful_request_can_dispatch_through_airtable(monkeypatch):
    calls = {"airtable": 0}

    def fake_dispatch(**kwargs):
        assert kwargs["airtable_enabled"] is True
        calls["airtable"] += 1
        return {
            "destinations": {
                "google_sheets": {"status": "disabled"},
                "airtable": {
                    "status": "success",
                    "result": {"status": "sent", "record_id": "rec123"},
                },
            },
        }

    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "AIRTABLE_ENABLED", True)
    monkeypatch.setattr(api_module, "dispatch_processed_lead_integrations", fake_dispatch)
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Forwarded-For": "airtable-route-client"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert "google_sheets" not in response.json()
    assert "airtable" not in response.json()
    assert calls["airtable"] == 1
