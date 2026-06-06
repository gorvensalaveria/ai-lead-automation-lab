from fastapi.testclient import TestClient
import pytest

import app.api as api_module
from app.automation.storage import build_result
from app.api import app
from app.rate_limiter import FixedWindowRateLimiter, RateLimitResult


client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_google_sheets_auto_append(monkeypatch):
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", False)


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


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_request_id_header_is_preserved():
    response = client.get("/health", headers={"X-Request-ID": "portfolio-request-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "portfolio-request-1"


def test_detailed_health_check_returns_operations_readiness():
    response = client.get("/health/details")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert "checked_at" in data
    assert "saved_leads" in data["counts"]
    assert data["checks"]["output_directory"]["status"] == "ok"
    assert data["checks"]["sqlite_database"]["status"] == "ok"
    assert data["workflow_version"] == "lead-intake-v1"


def test_system_status_page_returns_operations_html():
    response = client.get("/system-status")

    assert response.status_code == 200
    assert "System Status" in response.text
    assert "Operations Readiness" in response.text
    assert "Runtime and Storage Checks" in response.text
    assert 'href="/history"' in response.text
    assert 'href="/lead-intake"' in response.text


def test_lead_intake_page_returns_html_without_openai_call():
    response = client.get("/lead-intake")

    assert response.status_code == 200
    assert "AI Lead Qualification Assistant" in response.text
    assert "Process Lead" in response.text
    assert "Run the AI qualification workflow" in response.text
    assert "data-sample=\"warm\"" in response.text
    assert '<input name="email" type="email" required autocomplete="email">' in response.text
    assert 'href="/static/lead-intake.css"' in response.text
    assert 'src="/static/lead-intake.js"' in response.text
    assert "Built with Python, FastAPI, OpenAI API" in response.text


def test_lead_intake_static_assets_are_served():
    css_response = client.get("/static/lead-intake.css")
    js_response = client.get("/static/lead-intake.js")

    assert css_response.status_code == 200
    assert "classification-card" in css_response.text
    assert "detail-link" in css_response.text
    assert "copy-button" in css_response.text
    assert "score-value.hot" in css_response.text

    assert js_response.status_code == 200
    assert "budget not finalized" in js_response.text
    assert "sample lead loaded" in js_response.text
    assert '.replace(/\\n/g, "<br>")' in js_response.text
    assert "getSavedFileName" in js_response.text
    assert "Open saved lead details" in js_response.text
    assert "/webhooks/leads" in js_response.text
    assert "Too many lead processing attempts" in js_response.text
    assert "Try again in" in js_response.text


def test_history_page_returns_html_without_openai_call():
    response = client.get("/history")

    assert response.status_code == 200
    assert "Lead Review History" in response.text
    assert "Processed Lead History" in response.text
    assert "history-filters" in response.text
    assert "history-filter-link" in response.text
    assert "Filter by classification" in response.text
    assert 'href="/lead-intake"' in response.text


def test_history_page_accepts_filter_and_page_query_params():
    response = client.get("/history?classification=warm&page=2")

    assert response.status_code == 200
    assert "Lead Review History" in response.text
    assert "history-filter-link active" in response.text


def test_history_api_returns_leads_list_without_openai_call():
    response = client.get("/api/history")

    assert response.status_code == 200
    assert "leads" in response.json()
    assert isinstance(response.json()["leads"], list)


def test_bulk_status_rejects_invalid_file_names_payload():
    response = client.post(
        "/api/history/bulk-status",
        json={"file_names": "lead.json", "review_status": "reviewed"},
    )

    assert response.status_code == 400
    assert "file_names must be a list" in response.json()["detail"]


def test_bulk_status_rejects_empty_selection():
    response = client.post(
        "/api/history/bulk-status",
        json={"file_names": [], "review_status": "reviewed"},
    )

    assert response.status_code == 400
    assert "At least one saved output file name" in response.json()["detail"]


def test_history_csv_export_returns_downloadable_csv():
    response = client.get("/history/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "lead-history.csv" in response.headers["content-disposition"]
    assert response.text.startswith("processed_at,lead_id,contact_name")


def test_history_events_api_rejects_non_json_file_name():
    response = client.get("/api/history/missing-output.txt/events")

    assert response.status_code == 400
    assert "JSON file name only" in response.json()["detail"]


def test_google_sheets_preview_returns_handoff_shape():
    response = client.get("/api/integrations/google-sheets/preview")

    assert response.status_code == 200
    assert response.json()["integration"] == "google_sheets"
    assert "contact_name" in response.json()["columns"]
    assert "workflow_version" in response.json()["columns"]
    assert isinstance(response.json()["rows"], list)


def test_google_sheets_lead_preview_rejects_non_json_file_name():
    response = client.get("/api/integrations/google-sheets/preview/missing-output.txt")

    assert response.status_code == 400
    assert "JSON file name only" in response.json()["detail"]


def test_google_sheets_append_saved_lead_uses_live_integration(monkeypatch):
    def fake_load_saved_output(file_name):
        return sample_processed_result()

    def fake_append_result_to_google_sheet(result):
        return {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
            "updated_range": "Leads!A2:T2",
            "updated_rows": 1,
        }

    def fake_record_lead_event(**kwargs):
        return {"event_type": kwargs["event_type"]}

    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(api_module, "load_saved_output", fake_load_saved_output)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )
    monkeypatch.setattr(api_module, "record_lead_event", fake_record_lead_event)

    response = client.post("/api/integrations/google-sheets/append/lead_test.json")

    assert response.status_code == 200
    data = response.json()
    assert data["integration"] == "google_sheets"
    assert data["file_name"] == "lead_test.json"
    assert data["result"]["status"] == "appended"
    assert data["result"]["updated_range"] == "Leads!A2:T2"


def test_google_sheets_append_saved_lead_skips_duplicate_export(monkeypatch):
    def fake_append_result_to_google_sheet(result):
        raise AssertionError("Duplicate exports should not call Google Sheets.")

    monkeypatch.setattr(api_module, "load_saved_output", lambda file_name: sample_processed_result())
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: True)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )

    response = client.post("/api/integrations/google-sheets/append/lead_test.json")

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "skipped"
    assert response.json()["result"]["reason"] == "already_exported"


def test_google_sheets_append_saved_lead_skips_duplicate_email(monkeypatch):
    def fake_append_result_to_google_sheet(result):
        raise AssertionError("Duplicate emails should not call Google Sheets.")

    monkeypatch.setattr(api_module, "load_saved_output", lambda file_name: sample_processed_result())
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: True)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )

    response = client.post("/api/integrations/google-sheets/append/new_file_same_email.json")

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "skipped"
    assert "email" in response.json()["result"]["detail"]


def test_google_sheets_append_saved_lead_skips_duplicate_lead_id(monkeypatch):
    def fake_append_result_to_google_sheet(result):
        raise AssertionError("Duplicate lead IDs should not call Google Sheets.")

    monkeypatch.setattr(api_module, "load_saved_output", lambda file_name: sample_processed_result())
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: True)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )

    response = client.post("/api/integrations/google-sheets/append/lead_valid_later.json")

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "skipped"
    assert "lead ID" in response.json()["result"]["detail"]


def test_google_sheets_append_saved_lead_rejects_non_json_file_name():
    response = client.post("/api/integrations/google-sheets/append/missing-output.txt")

    assert response.status_code == 400
    assert "JSON file name only" in response.json()["detail"]


def test_archive_lead_rejects_non_json_file_name():
    response = client.post("/api/history/missing-output.txt/archive")

    assert response.status_code == 400
    assert "JSON file name only" in response.json()["detail"]


def test_history_detail_page_returns_404_for_missing_output():
    response = client.get("/history/missing-output.json")

    assert response.status_code == 404
    assert "Saved output not found" in response.json()["detail"]


def test_history_detail_api_rejects_non_json_file_name():
    response = client.get("/api/history/missing-output.txt")

    assert response.status_code == 400
    assert "JSON file name only" in response.json()["detail"]


def test_lead_webhook_rejects_invalid_lead_without_openai_call():
    response = client.post(
        "/webhooks/leads",
        json={
            "lead_id": "lead_invalid",
            "source": "website_form",
        },
    )

    assert response.status_code == 400
    assert "missing required top-level fields" in response.json()["detail"]


def test_lead_webhook_sanitizes_ai_processing_errors(monkeypatch):
    def raise_provider_error(lead):
        raise RuntimeError(
            "OpenAI summary request failed: Error code: 401 - Incorrect API key "
            "provided: sk-proj-secret"
        )

    monkeypatch.setattr(api_module, "process_lead", raise_provider_error)

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Request-ID": "qa-error-1"},
    )

    detail = response.json()["detail"]

    assert response.status_code == 502
    assert "AI processing is unavailable right now" in detail
    assert "Reference ID: qa-error-1" in detail
    assert "Incorrect API key" not in detail
    assert "sk-proj" not in detail
    assert "OpenAI summary request failed" not in detail


def test_lead_webhook_rate_limit_returns_retry_after(monkeypatch):
    class BlockedLimiter:
        def check(self, key):
            return RateLimitResult(
                allowed=False,
                limit=1,
                remaining=0,
                retry_after_seconds=42,
                reset_seconds=42,
            )

    monkeypatch.setattr(api_module, "lead_process_rate_limiter", BlockedLimiter())

    response = client.post("/webhooks/leads", json=valid_lead_payload())

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "42"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "Lead processing rate limit exceeded" in response.json()["detail"]


def test_lead_webhook_blocks_fourth_request_in_sixty_second_window(monkeypatch):
    def process_without_openai(lead):
        return {"lead_id": lead["lead_id"]}, "data/outputs/lead_valid.json"

    monkeypatch.setattr(api_module, "process_lead", process_without_openai)
    monkeypatch.setattr(
        api_module,
        "lead_process_rate_limiter",
        FixedWindowRateLimiter(limit=3, window_seconds=60, clock=lambda: 100.0),
    )

    responses = [
        client.post(
            "/webhooks/leads",
            json=valid_lead_payload(),
            headers={"X-Forwarded-For": "qa-rate-limit-client"},
        )
        for _ in range(4)
    ]

    assert [response.status_code for response in responses] == [200, 200, 200, 429]
    assert responses[2].headers["X-RateLimit-Remaining"] == "0"
    assert responses[3].headers["Retry-After"] == "60"


def test_lead_webhook_auto_appends_to_google_sheets_when_enabled(monkeypatch):
    def process_without_openai(lead):
        return sample_processed_result(), "data/outputs/lead_valid.json"

    def fake_append_result_to_google_sheet(result):
        return {
            "status": "appended",
            "spreadsheet_id": "sheet_123",
            "updated_range": "Leads!A2:T2",
        }

    def fake_record_lead_event(**kwargs):
        return {"event_type": kwargs["event_type"]}

    monkeypatch.setattr(api_module, "process_lead", process_without_openai)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: False)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )
    monkeypatch.setattr(api_module, "record_lead_event", fake_record_lead_event)
    monkeypatch.setattr(
        api_module,
        "lead_process_rate_limiter",
        FixedWindowRateLimiter(limit=3, window_seconds=60, clock=lambda: 200.0),
    )

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Forwarded-For": "qa-google-sheets-client"},
    )

    assert response.status_code == 200
    assert response.json()["google_sheets"]["status"] == "appended"
    assert response.json()["google_sheets"]["updated_range"] == "Leads!A2:T2"


def test_lead_webhook_auto_append_skips_duplicate_export(monkeypatch):
    def process_without_openai(lead):
        return sample_processed_result(), "data/outputs/lead_valid.json"

    def fake_append_result_to_google_sheet(result):
        raise AssertionError("Duplicate exports should not call Google Sheets.")

    monkeypatch.setattr(api_module, "process_lead", process_without_openai)
    monkeypatch.setattr(api_module, "GOOGLE_SHEETS_AUTO_APPEND", True)
    monkeypatch.setattr(api_module, "has_lead_event", lambda file_name, event_type: True)
    monkeypatch.setattr(api_module, "has_exported_email_to_google_sheets", lambda email: False)
    monkeypatch.setattr(api_module, "has_exported_lead_to_google_sheets", lambda lead_id: False)
    monkeypatch.setattr(
        api_module,
        "append_result_to_google_sheet",
        fake_append_result_to_google_sheet,
    )
    monkeypatch.setattr(
        api_module,
        "lead_process_rate_limiter",
        FixedWindowRateLimiter(limit=3, window_seconds=60, clock=lambda: 250.0),
    )

    response = client.post(
        "/webhooks/leads",
        json=valid_lead_payload(),
        headers={"X-Forwarded-For": "qa-google-sheets-duplicate-client"},
    )

    assert response.status_code == 200
    assert response.json()["google_sheets"]["status"] == "skipped"
    assert response.json()["google_sheets"]["reason"] == "already_exported"
