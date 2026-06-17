import sqlite3

from app.automation import storage
from app.automation.storage import build_result
from app.integrations.dispatcher import dispatch_processed_lead_integrations


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


def test_integration_runs_table_is_created(tmp_path):
    database_path = storage.initialize_database(tmp_path)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'integration_runs'
            """
        ).fetchone()

    assert row is not None


def test_create_list_and_get_integration_run(tmp_path):
    run_id = storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="airtable",
        status="success",
        external_id="rec123",
        message="success",
        response_json={"status": "success", "result": {"record_id": "rec123"}},
        output_dir=tmp_path,
    )

    runs = storage.list_integration_runs(output_dir=tmp_path)
    run = storage.get_integration_run(run_id, output_dir=tmp_path)

    assert runs == [
        {
            "id": run_id,
            "file_name": "lead_valid.json",
            "lead_id": "lead_valid",
            "provider": "airtable",
            "status": "success",
            "external_id": "rec123",
            "message": "success",
            "retry_count": 0,
            "last_retry_at": None,
            "created_at": runs[0]["created_at"],
            "updated_at": runs[0]["updated_at"],
        }
    ]
    assert "response_json" not in runs[0]
    assert run["response_json"]["result"]["record_id"] == "rec123"


def test_list_integration_runs_filters_by_provider_and_status(tmp_path):
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

    provider_runs = storage.list_integration_runs(provider="hubspot", output_dir=tmp_path)
    failed_runs = storage.list_integration_runs(status="failed", output_dir=tmp_path)

    assert [run["provider"] for run in provider_runs] == ["hubspot"]
    assert [run["status"] for run in failed_runs] == ["failed"]


def test_update_integration_run_after_retry_increments_retry_count(tmp_path):
    run_id = storage.create_integration_run(
        file_name="lead_valid.json",
        lead_id="lead_valid",
        provider="hubspot",
        status="failed",
        output_dir=tmp_path,
    )

    storage.update_integration_run_after_retry(
        run_id=run_id,
        status="failed",
        message="HubSpot delivery failed.",
        response_json={"status": "failed", "error": "HubSpot delivery failed."},
        output_dir=tmp_path,
    )
    storage.update_integration_run_after_retry(
        run_id=run_id,
        status="success",
        external_id="contact_123",
        response_json={"status": "success", "result": {"object_id": "contact_123"}},
        output_dir=tmp_path,
    )

    run = storage.get_integration_run(run_id, output_dir=tmp_path)
    assert run["status"] == "success"
    assert run["retry_count"] == 2
    assert run["last_retry_at"]
    assert run["external_id"] == "contact_123"


def test_integration_status_summary_counts_by_provider(tmp_path):
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
        provider="airtable",
        status="failed",
        output_dir=tmp_path,
    )

    summary = storage.get_integration_status_summary(output_dir=tmp_path)

    assert summary["airtable"]["last_status"] == "failed"
    assert summary["airtable"]["success_count"] == 1
    assert summary["airtable"]["failed_count"] == 1


def test_dispatcher_records_success_and_failed_runs_but_not_disabled():
    recorded = []

    def fake_recorder(**kwargs):
        recorded.append(kwargs)
        return len(recorded)

    def fake_airtable(**kwargs):
        return {"status": "sent", "record_id": "rec123"}

    result = dispatch_processed_lead_integrations(
        result=sample_processed_result(),
        output_path="data/outputs/lead_valid.json",
        google_sheets_auto_append=True,
        airtable_enabled=True,
        hubspot_enabled=False,
        duplicate_export_checker=lambda result, file_name: "",
        append_google_sheets_result=lambda result: {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
        },
        send_airtable_record=fake_airtable,
        record_event=lambda **kwargs: {"event_type": kwargs["event_type"]},
        record_integration_runs=True,
        integration_run_recorder=fake_recorder,
    )

    assert result["destinations"]["hubspot"]["status"] == "disabled"
    assert [run["provider"] for run in recorded] == ["google_sheets", "airtable"]
    assert [run["status"] for run in recorded] == ["success", "success"]
    assert recorded[0]["external_id"] == "sheet_123"
    assert recorded[1]["external_id"] == "rec123"
