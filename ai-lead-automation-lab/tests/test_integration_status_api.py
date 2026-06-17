from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation import storage


client = TestClient(app)


def use_temp_run_listing(monkeypatch, tmp_path):
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


def test_integration_runs_api_returns_safe_fields(monkeypatch, tmp_path):
    use_temp_run_listing(monkeypatch, tmp_path)
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        message="HubSpot delivery failed.",
        response_json={"status": "failed", "error": "secret-ish internal payload"},
        output_dir=tmp_path,
    )

    response = client.get("/api/integrations/runs")
    run = response.json()["runs"][0]

    assert response.status_code == 200
    assert run["provider"] == "hubspot"
    assert run["status"] == "failed"
    assert run["file_name"] == "lead_valid.json"
    assert "response_json" not in run
    assert "data/outputs" not in str(run)
    assert "Authorization" not in str(run)


def test_integration_runs_api_query_filters_work(monkeypatch, tmp_path):
    use_temp_run_listing(monkeypatch, tmp_path)
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="airtable",
        status="success",
        output_dir=tmp_path,
    )
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        output_dir=tmp_path,
    )

    response = client.get("/api/integrations/runs?provider=hubspot&status=failed")

    assert response.status_code == 200
    assert len(response.json()["runs"]) == 1
    assert response.json()["runs"][0]["provider"] == "hubspot"


def test_integration_runs_api_rejects_unsafe_file_name(monkeypatch, tmp_path):
    use_temp_run_listing(monkeypatch, tmp_path)

    response = client.get("/api/integrations/runs?file_name=../secret.json")

    assert response.status_code == 400
    assert "file name" in response.json()["detail"]


def test_integration_status_api_returns_provider_summary(monkeypatch, tmp_path):
    use_temp_run_listing(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    monkeypatch.setattr(api_module, "AIRTABLE_ENABLED", False)
    monkeypatch.setattr(api_module, "HUBSPOT_ENABLED", True)
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="google_sheets",
        status="success",
        output_dir=tmp_path,
    )
    storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        output_dir=tmp_path,
    )

    response = client.get("/api/integrations/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["providers"]["google_sheets"]["enabled"] is True
    assert payload["providers"]["google_sheets"]["last_status"] == "success"
    assert payload["providers"]["airtable"]["enabled"] is False
    assert payload["providers"]["airtable"]["last_status"] == "disabled"
    assert payload["providers"]["hubspot"]["failed_count"] == 1
    assert payload["failed_total"] == 1
