from app.automation.storage import build_result
from app.integrations.google_sheets import (
    GOOGLE_SHEETS_COLUMNS,
    build_google_sheets_payload,
    build_google_sheets_row,
    build_google_sheets_values,
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
