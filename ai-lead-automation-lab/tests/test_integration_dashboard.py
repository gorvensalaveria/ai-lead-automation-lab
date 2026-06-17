from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation import storage
from app.automation.storage import build_result, save_output


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
        "list_integration_runs",
        lambda **kwargs: storage.list_integration_runs(output_dir=tmp_path, **kwargs),
    )
    monkeypatch.setattr(
        api_module,
        "get_integration_status_summary",
        lambda: storage.get_integration_status_summary(output_dir=tmp_path),
    )
    monkeypatch.setattr(
        api_module,
        "get_integration_run",
        lambda run_id: storage.get_integration_run(run_id, output_dir=tmp_path),
    )
    monkeypatch.setattr(
        api_module,
        "update_integration_run_after_retry",
        lambda **kwargs: storage.update_integration_run_after_retry(
            **{**kwargs, "output_dir": tmp_path},
        ),
    )
    monkeypatch.setattr(
        api_module,
        "load_saved_output",
        lambda file_name: storage.load_saved_output(file_name, output_dir=tmp_path),
    )


def test_system_status_page_includes_integration_dashboard():
    response = client.get("/system-status")

    assert response.status_code == 200
    assert "Integration Status" in response.text
    assert "Recent Failed Integration Runs" in response.text
    assert "data-integration-dashboard" in response.text


def test_dashboard_references_integration_api_endpoints():
    response = client.get("/system-status")

    assert "/api/integrations/status" in response.text
    assert "/api/integrations/runs?status=failed" in response.text
    assert "/api/integrations/retry/" in response.text


def test_dashboard_output_does_not_expose_internal_or_secret_fields():
    response = client.get("/system-status")

    assert "response_json" not in response.text
    assert "Authorization" not in response.text
    assert "Bearer " not in response.text
    assert "HUBSPOT_ACCESS_TOKEN" not in response.text
    assert "AIRTABLE_API_KEY" not in response.text
    assert "WEBHOOK_API_KEY" not in response.text


def test_integration_status_api_still_returns_provider_summary(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="google_sheets",
        status="success",
        output_dir=tmp_path,
    )

    response = client.get("/api/integrations/status")

    assert response.status_code == 200
    assert set(response.json()["providers"]) == {
        "google_sheets",
        "airtable",
        "hubspot",
    }
    assert response.json()["providers"]["google_sheets"]["success_count"] == 1


def test_integration_runs_api_can_return_failed_runs(monkeypatch, tmp_path):
    use_temp_integration_store(monkeypatch, tmp_path)
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        message="HubSpot delivery failed.",
        output_dir=tmp_path,
    )

    response = client.get("/api/integrations/runs?status=failed")
    run = response.json()["runs"][0]

    assert response.status_code == 200
    assert run["status"] == "failed"
    assert run["provider"] == "hubspot"
    assert run["file_name"] == "lead_valid.json"
    assert "response_json" not in run


def test_retry_api_response_remains_dashboard_compatible(monkeypatch, tmp_path):
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
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["run_id"] == run_id
    assert payload["provider"] == "airtable"
    assert payload["retry_count"] == 1
    assert "result" in payload
