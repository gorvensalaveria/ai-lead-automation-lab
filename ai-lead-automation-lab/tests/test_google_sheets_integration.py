from app.automation.storage import build_result
from app.integrations.google_sheets import (
    GOOGLE_SHEETS_COLUMNS,
    GoogleSheetsConfigError,
    append_result_to_google_sheet,
    build_google_sheets_payload,
    build_google_sheets_row,
    build_google_sheets_values,
    post_google_sheets_append_request,
)


def sample_lead() -> dict:
    return {
        "lead_id": "lead_test",
        "source": "website_form",
        "submitted_at": "2026-05-22T10:00:00+08:00",
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
            "budget_range": "USD 1,000 - USD 2,000",
            "timeline": "urgent",
            "preferred_contact_method": "email",
        },
    }


def sample_score() -> dict:
    return {
        "total_score": 100,
        "max_score": 100,
        "rating": "high",
        "breakdown": {
            "fit": 25,
            "urgency": 25,
            "budget": 25,
            "intent": 25,
        },
    }


def sample_result() -> dict:
    return build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )


def test_google_sheets_row_contains_crm_ready_fields():
    row = build_google_sheets_row(sample_result())

    assert list(row.keys()) == GOOGLE_SHEETS_COLUMNS
    assert row["contact_name"] == "Ana Santos"
    assert row["company"] == "Santos Software"
    assert row["classification"] == "hot"
    assert row["lead_score"] == 100
    assert row["review_status"] == "new"
    assert row["workflow_version"] == "lead-intake-v1"
    assert row["model"]


def test_google_sheets_payload_matches_append_shape():
    result = sample_result()
    payload = build_google_sheets_payload(result)
    values = build_google_sheets_values(result)

    assert payload["range"] == "Leads!A:T"
    assert payload["majorDimension"] == "ROWS"
    assert payload["columns"] == GOOGLE_SHEETS_COLUMNS
    assert payload["values"] == [values]
    assert len(values) == len(GOOGLE_SHEETS_COLUMNS)


def test_google_sheets_live_append_requires_configuration(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.google_sheets.GOOGLE_SHEETS_ENABLED",
        False,
    )

    try:
        append_result_to_google_sheet(sample_result())
    except GoogleSheetsConfigError as error:
        assert "GOOGLE_SHEETS_ENABLED=true" in str(error)
    else:
        raise AssertionError("Expected GoogleSheetsConfigError")


def test_google_sheets_append_request_uses_requests_client(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "spreadsheetId": "sheet_123",
                "updates": {
                    "updatedRange": "Leads!A2:T2",
                    "updatedRows": 1,
                },
            }

    captured_request = {}

    def fake_post(url, json, headers, timeout):
        captured_request["url"] = url
        captured_request["json"] = json
        captured_request["headers"] = headers
        captured_request["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.integrations.google_sheets.requests.post", fake_post)
    monkeypatch.setattr(
        "app.integrations.google_sheets.GOOGLE_SHEETS_SPREADSHEET_ID",
        "sheet_123",
    )

    result = post_google_sheets_append_request(
        access_token="token_123",
        payload={"values": [["Ana Santos"]]},
    )

    assert result["spreadsheetId"] == "sheet_123"
    assert "values/Leads%21A%3AT:append" in captured_request["url"]
    assert "valueInputOption=RAW" in captured_request["url"]
    assert captured_request["json"] == {"values": [["Ana Santos"]]}
    assert captured_request["headers"] == {"Authorization": "Bearer token_123"}
    assert captured_request["timeout"] == 20
