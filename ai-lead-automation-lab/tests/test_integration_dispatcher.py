from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation.storage import build_result
from app.integrations.dispatcher import (
    build_legacy_google_sheets_response,
    dispatch_processed_lead_integrations,
)
from app.integrations.airtable import AirtableConfigError
from app.integrations.google_sheets import (
    GoogleSheetsAppendError,
    GoogleSheetsConfigError,
)
from app.integrations.hubspot import HubSpotConfigError


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


def test_dispatcher_marks_google_sheets_disabled():
    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
    )

    assert result == {
        "destinations": {
            "google_sheets": {
                "status": "disabled",
            },
            "airtable": {
                "status": "disabled",
            },
            "hubspot": {
                "status": "disabled",
            },
        },
    }
    assert build_legacy_google_sheets_response(result) is None


def test_dispatcher_calls_google_sheets_when_enabled():
    calls = {"append": 0, "event": 0}

    def fake_append(result):
        calls["append"] += 1
        return {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
            "updated_range": "Leads!A2:T2",
        }

    def fake_record_event(**kwargs):
        calls["event"] += 1
        return {"event_type": kwargs["event_type"]}

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        duplicate_export_checker=lambda result, file_name: "",
        append_google_sheets_result=fake_append,
        record_event=fake_record_event,
    )

    destination = result["destinations"]["google_sheets"]
    assert destination["status"] == "success"
    assert destination["result"]["status"] == "appended"
    assert destination["result"]["updated_range"] == "Leads!A2:T2"
    assert calls == {"append": 1, "event": 1}
    assert result["destinations"]["airtable"]["status"] == "disabled"
    assert result["destinations"]["hubspot"]["status"] == "disabled"
    assert build_legacy_google_sheets_response(result)["status"] == "appended"


def test_dispatcher_returns_skipped_for_duplicate_google_sheets_export():
    def fail_if_called(result):
        raise AssertionError("Duplicate export should not append.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        duplicate_export_checker=lambda result, file_name: "Already exported.",
        append_google_sheets_result=fail_if_called,
    )

    destination = result["destinations"]["google_sheets"]
    assert destination["status"] == "skipped"
    assert destination["reason"] == "already_exported"
    assert destination["detail"] == "Already exported."
    assert result["destinations"]["airtable"]["status"] == "disabled"
    assert result["destinations"]["hubspot"]["status"] == "disabled"
    assert build_legacy_google_sheets_response(result)["status"] == "skipped"


def test_dispatcher_returns_failed_safely_for_google_sheets_config_error():
    def raise_config_error(result):
        raise GoogleSheetsConfigError("GOOGLE_SHEETS_SPREADSHEET_ID is missing.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        duplicate_export_checker=lambda result, file_name: "",
        append_google_sheets_result=raise_config_error,
    )

    destination = result["destinations"]["google_sheets"]
    assert destination["status"] == "failed"
    assert destination["error"] == "GOOGLE_SHEETS_SPREADSHEET_ID is missing."
    assert "Traceback" not in destination["error"]
    assert build_legacy_google_sheets_response(result) == {
        "status": "failed",
        "detail": "GOOGLE_SHEETS_SPREADSHEET_ID is missing.",
    }


def test_dispatcher_returns_failed_safely_for_google_sheets_append_error():
    def raise_append_error(result):
        raise GoogleSheetsAppendError("Google Sheets append request failed: 503")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        duplicate_export_checker=lambda result, file_name: "",
        append_google_sheets_result=raise_append_error,
    )

    destination = result["destinations"]["google_sheets"]
    assert destination["status"] == "failed"
    assert destination["error"] == "Google Sheets append request failed: 503"
    assert "Traceback" not in destination["error"]


def test_webhook_route_calls_dispatcher_on_successful_new_request(monkeypatch):
    calls = {"dispatcher": 0}

    def fake_dispatch(**kwargs):
        calls["dispatcher"] += 1
        assert kwargs["output_path"] == "data/outputs/lead_valid.json"
        return {
            "destinations": {
                "google_sheets": {
                    "status": "disabled",
                },
                "airtable": {
                    "status": "disabled",
                },
                "hubspot": {
                    "status": "disabled",
                },
            },
        }

    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "dispatch_processed_lead_integrations", fake_dispatch)
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Forwarded-For": "dispatcher-route-client"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert "google_sheets" not in response.json()
    assert calls["dispatcher"] == 1


def test_dispatcher_calls_airtable_when_enabled():
    calls = {"airtable": 0}

    def fake_send_airtable_record(**kwargs):
        calls["airtable"] += 1
        assert kwargs["output_path"] == "data/outputs/lead_valid.json"
        assert kwargs["enabled"] is True
        return {"status": "sent", "record_id": "rec123"}

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        airtable_enabled=True,
        send_airtable_record=fake_send_airtable_record,
    )

    assert result["destinations"]["google_sheets"]["status"] == "disabled"
    assert result["destinations"]["airtable"] == {
        "status": "success",
        "result": {
            "status": "sent",
            "record_id": "rec123",
        },
    }
    assert calls["airtable"] == 1


def test_dispatcher_does_not_call_airtable_when_disabled():
    def fail_if_called(**kwargs):
        raise AssertionError("Disabled Airtable destination should not send.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        airtable_enabled=False,
        send_airtable_record=fail_if_called,
    )

    assert result["destinations"]["airtable"]["status"] == "disabled"


def test_dispatcher_returns_failed_for_missing_airtable_config():
    def raise_airtable_config_error(**kwargs):
        raise AirtableConfigError("Airtable integration is enabled but not configured.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        airtable_enabled=True,
        send_airtable_record=raise_airtable_config_error,
    )

    destination = result["destinations"]["airtable"]
    assert destination["status"] == "failed"
    assert destination["error"] == "Airtable integration is enabled but not configured."
    assert "Traceback" not in destination["error"]


def test_dispatcher_calls_hubspot_when_enabled():
    calls = {"hubspot": 0}

    def fake_send_hubspot_contact(**kwargs):
        calls["hubspot"] += 1
        assert kwargs["enabled"] is True
        return {"status": "sent", "object_id": "contact_123"}

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        airtable_enabled=False,
        hubspot_enabled=True,
        send_hubspot_contact=fake_send_hubspot_contact,
    )

    assert result["destinations"]["google_sheets"]["status"] == "disabled"
    assert result["destinations"]["airtable"]["status"] == "disabled"
    assert result["destinations"]["hubspot"] == {
        "status": "success",
        "result": {
            "status": "sent",
            "object_id": "contact_123",
        },
    }
    assert calls["hubspot"] == 1


def test_dispatcher_does_not_call_hubspot_when_disabled():
    def fail_if_called(**kwargs):
        raise AssertionError("Disabled HubSpot destination should not send.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        hubspot_enabled=False,
        send_hubspot_contact=fail_if_called,
    )

    assert result["destinations"]["hubspot"]["status"] == "disabled"


def test_dispatcher_returns_failed_for_missing_hubspot_config():
    def raise_hubspot_config_error(**kwargs):
        raise HubSpotConfigError("HubSpot integration is enabled but not configured.")

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        hubspot_enabled=True,
        send_hubspot_contact=raise_hubspot_config_error,
    )

    destination = result["destinations"]["hubspot"]
    assert destination["status"] == "failed"
    assert destination["error"] == "HubSpot integration is enabled but not configured."
    assert "Traceback" not in destination["error"]


def test_dispatcher_includes_all_destination_statuses():
    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=False,
        airtable_enabled=False,
        hubspot_enabled=False,
    )

    assert set(result["destinations"]) == {
        "google_sheets",
        "airtable",
        "hubspot",
    }
