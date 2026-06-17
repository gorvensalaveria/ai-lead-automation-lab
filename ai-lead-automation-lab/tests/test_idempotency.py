from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app
from app.automation import storage
from app.automation.storage import (
    build_result,
    load_idempotency_response,
    save_idempotency_response,
)


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


def use_temp_idempotency_store(monkeypatch, tmp_path):
    monkeypatch.setattr(
        api_module,
        "load_idempotency_response",
        lambda idempotency_key: load_idempotency_response(
            idempotency_key,
            output_dir=tmp_path,
        ),
    )
    monkeypatch.setattr(
        api_module,
        "save_idempotency_response",
        lambda **kwargs: save_idempotency_response(
            output_dir=tmp_path,
            **kwargs,
        ),
    )


def test_storage_saves_and_loads_idempotency_response(tmp_path):
    response_payload = {
        "status": "processed",
        "output_path": "data/outputs/lead_valid.json",
        "result": {"lead": {"lead_id": "lead_valid"}},
    }

    save_idempotency_response(
        idempotency_key="idem-storage-1",
        response_payload=response_payload,
        lead_id="lead_valid",
        file_name="lead_valid.json",
        output_dir=tmp_path,
    )

    saved_response = load_idempotency_response(
        "idem-storage-1",
        output_dir=tmp_path,
    )

    assert saved_response == response_payload


def test_first_request_with_idempotency_key_processes_normally(monkeypatch, tmp_path):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={
            "Idempotency-Key": "idem-first-request",
            "X-Forwarded-For": "idem-first-client",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert load_idempotency_response(
        "idem-first-request",
        output_dir=tmp_path,
    ) == response.json()


def test_duplicate_idempotency_key_returns_saved_response_without_processing(
    monkeypatch,
    tmp_path,
):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    call_count = {"process_lead": 0}

    def process_once(lead):
        call_count["process_lead"] += 1
        return sample_processed_result(), "data/outputs/lead_valid.json"

    monkeypatch.setattr(api_module, "process_lead", process_once)

    headers = {
        "Idempotency-Key": "idem-duplicate-request",
        "X-Forwarded-For": "idem-duplicate-client",
    }
    first_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )
    second_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    assert call_count["process_lead"] == 1


def test_duplicate_idempotency_key_does_not_append_to_google_sheets_again(
    monkeypatch,
    tmp_path,
):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    append_count = {"google_sheets": 0}

    def fake_append_result_to_google_sheet(result):
        append_count["google_sheets"] += 1
        return {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
            "updated_range": "Leads!A2:T2",
        }

    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )
    monkeypatch.setattr(
        api_module,
        "record_lead_event",
        lambda **kwargs: {"event_type": kwargs["event_type"]},
    )
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    headers = {
        "Idempotency-Key": "idem-google-sheets",
        "X-Forwarded-For": "idem-google-sheets-client",
    }
    first_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )
    second_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["google_sheets"]["status"] == "appended"
    assert second_response.json() == first_response.json()
    assert append_count["google_sheets"] == 1


def test_duplicate_idempotency_key_does_not_call_dispatcher_again(
    monkeypatch,
    tmp_path,
):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    dispatch_count = {"integrations": 0}

    def fake_dispatch(**kwargs):
        dispatch_count["integrations"] += 1
        return {
            "destinations": {
                "google_sheets": {
                    "status": "disabled",
                },
            },
        }

    monkeypatch.setattr(api_module, "dispatch_processed_lead_integrations", fake_dispatch)
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    headers = {
        "Idempotency-Key": "idem-dispatcher-count",
        "X-Forwarded-For": "idem-dispatcher-count-client",
    }
    first_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )
    second_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    assert dispatch_count["integrations"] == 1


def test_duplicate_idempotency_key_does_not_create_duplicate_integration_runs(
    monkeypatch,
    tmp_path,
):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        lambda result: {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
            "updated_range": "Leads!A2:T2",
        },
    )
    monkeypatch.setattr(
        api_module,
        "record_lead_event",
        lambda **kwargs: {"event_type": kwargs["event_type"]},
    )
    monkeypatch.setattr(
        api_module,
        "create_integration_run",
        lambda **kwargs: storage.create_integration_run(
            **{**kwargs, "output_dir": tmp_path},
        ),
    )
    monkeypatch.setattr(
        api_module,
        "process_lead",
        lambda lead: (sample_processed_result(), "data/outputs/lead_valid.json"),
    )

    headers = {
        "Idempotency-Key": "idem-integration-runs",
        "X-Forwarded-For": "idem-integration-runs-client",
    }
    first_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )
    second_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    assert len(storage.list_integration_runs(output_dir=tmp_path)) == 1


def test_duplicate_idempotency_key_does_not_create_second_output(
    monkeypatch,
    tmp_path,
):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)
    created_outputs = []

    def process_once(lead):
        file_name = f"lead_valid_{len(created_outputs) + 1}.json"
        output_path = f"data/outputs/{file_name}"
        created_outputs.append(output_path)
        return sample_processed_result(), output_path

    monkeypatch.setattr(api_module, "process_lead", process_once)

    headers = {
        "Idempotency-Key": "idem-output-count",
        "X-Forwarded-For": "idem-output-count-client",
    }
    first_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )
    second_response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(created_outputs) == 1
    assert second_response.json()["output_path"] == created_outputs[0]


def test_failed_response_is_not_saved_for_idempotency_key(monkeypatch, tmp_path):
    use_temp_idempotency_store(monkeypatch, tmp_path)
    monkeypatch.setattr(api_module, "WEBHOOK_AUTH_ENABLED", False)
    monkeypatch.setattr(api_module, "WEBHOOK_HMAC_ENABLED", False)

    response = client.post(
        "/webhooks/leads",
        json={"lead_id": "invalid"},
        headers={
            "Idempotency-Key": "idem-failed-response",
            "X-Forwarded-For": "idem-failed-client",
        },
    )

    assert response.status_code == 400
    assert load_idempotency_response(
        "idem-failed-response",
        output_dir=tmp_path,
    ) is None


def test_idempotency_table_is_created_with_database(tmp_path):
    database_path = storage.initialize_database(tmp_path)

    import sqlite3

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'idempotency_keys'
            """
        ).fetchone()

    assert row is not None
