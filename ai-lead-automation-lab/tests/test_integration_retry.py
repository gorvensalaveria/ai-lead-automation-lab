from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation import storage
from app.automation.storage import build_result, save_output
from app.integrations.dispatcher import retry_integration_destination


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


def use_temp_integration_store(monkeypatch, tmp_path):
    monkeypatch.setattr(
        api_module,
        "get_integration_run",
        lambda run_id: storage.get_integration_run(run_id, output_dir=tmp_path),
    )
    monkeypatch.setattr(
        api_module,
        "update_integration_run_after_retry",
        lambda **kwargs: storage.update_integration_run_after_retry(
            output_dir=tmp_path,
            **kwargs,
        ),
    )
    monkeypatch.setattr(
        api_module,
        "load_saved_output",
        lambda file_name: storage.load_saved_output(file_name, output_dir=tmp_path),
    )


def test_retry_missing_run_returns_404(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)

    response = client.post("/api/integrations/retry/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Integration run not found."


def test_retry_non_failed_run_returns_400(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    save_output(sample_processed_result(), output_dir=tmp_path)
    run_id = storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="airtable",
        status="success",
        output_dir=tmp_path,
    )

    response = client.post(f"/api/integrations/retry/{run_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Only failed integration runs can be retried."


def test_successful_retry_updates_existing_failed_run(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    file_path = save_output(sample_processed_result(), output_dir=tmp_path)
    run_id = storage.create_integration_run(
        file_name=file_path.name,
        lead_id="lead_valid",
        provider="airtable",
        status="failed",
        output_dir=tmp_path,
    )

    monkeypatch.setattr(
        api_module,
        "retry_integration_destination",
        lambda **kwargs: {
            "status": "success",
            "result": {"status": "sent", "record_id": "rec123"},
        },
    )

    response = client.post(f"/api/integrations/retry/{run_id}")
    updated_run = storage.get_integration_run(run_id, output_dir=tmp_path)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["retry_count"] == 1
    assert updated_run["status"] == "success"
    assert updated_run["retry_count"] == 1
    assert updated_run["external_id"] == "rec123"


def test_failed_retry_increments_count_and_remains_failed(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    file_path = save_output(sample_processed_result(), output_dir=tmp_path)
    run_id = storage.create_integration_run(
        file_name=file_path.name,
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        output_dir=tmp_path,
    )

    monkeypatch.setattr(
        api_module,
        "retry_integration_destination",
        lambda **kwargs: {"status": "failed", "error": "HubSpot delivery failed."},
    )

    response = client.post(f"/api/integrations/retry/{run_id}")
    updated_run = storage.get_integration_run(run_id, output_dir=tmp_path)

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert updated_run["status"] == "failed"
    assert updated_run["retry_count"] == 1
    assert updated_run["message"] == "HubSpot delivery failed."


def test_retry_missing_saved_output_returns_404(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    run_id = storage.create_integration_run(
        file_name="missing.json",
        lead_id="lead_valid",
        provider="airtable",
        status="failed",
        output_dir=tmp_path,
    )

    response = client.post(f"/api/integrations/retry/{run_id}")

    assert response.status_code == 404
    assert "Saved output not found" in response.json()["detail"]


def test_unknown_provider_retry_returns_safe_failure():
    result = retry_integration_destination(
        provider="unknown",
        processed_lead=sample_processed_result(),
    )

    assert result == {
        "status": "failed",
        "error": "Unknown integration provider.",
    }


def test_retry_dispatches_only_requested_airtable_provider():
    calls = {"airtable": 0, "hubspot": 0, "google_sheets": 0}

    result = retry_integration_destination(
        provider="airtable",
        processed_lead=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        airtable_enabled=True,
        send_airtable_record=lambda **kwargs: calls.__setitem__("airtable", 1)
        or {"status": "sent", "record_id": "rec123"},
        send_hubspot_contact=lambda **kwargs: calls.__setitem__("hubspot", 1),
        append_google_sheets_result=lambda result: calls.__setitem__("google_sheets", 1),
    )

    assert result["status"] == "success"
    assert calls == {"airtable": 1, "hubspot": 0, "google_sheets": 0}


def test_retry_dispatches_only_requested_hubspot_provider():
    calls = {"airtable": 0, "hubspot": 0, "google_sheets": 0}

    result = retry_integration_destination(
        provider="hubspot",
        processed_lead=sample_processed_result(),
        hubspot_enabled=True,
        send_hubspot_contact=lambda **kwargs: calls.__setitem__("hubspot", 1)
        or {"status": "sent", "object_id": "contact_123"},
        send_airtable_record=lambda **kwargs: calls.__setitem__("airtable", 1),
        append_google_sheets_result=lambda result: calls.__setitem__("google_sheets", 1),
    )

    assert result["status"] == "success"
    assert calls == {"airtable": 0, "hubspot": 1, "google_sheets": 0}


def test_retry_dispatches_only_requested_google_sheets_provider():
    calls = {"airtable": 0, "hubspot": 0, "google_sheets": 0}

    result = retry_integration_destination(
        provider="google_sheets",
        processed_lead=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        duplicate_export_checker=lambda result, file_name: "",
        append_google_sheets_result=lambda result: calls.__setitem__("google_sheets", 1)
        or {"status": "appended", "spreadsheet_id": "sheet_123"},
        record_event=lambda **kwargs: {"event_type": kwargs["event_type"]},
        send_airtable_record=lambda **kwargs: calls.__setitem__("airtable", 1),
        send_hubspot_contact=lambda **kwargs: calls.__setitem__("hubspot", 1),
    )

    assert result["status"] == "success"
    assert calls == {"airtable": 0, "hubspot": 0, "google_sheets": 1}
