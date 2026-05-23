import json

import pytest

from app.automation.lead_loader import find_missing_fields, load_lead, validate_lead


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


def test_load_lead_reads_valid_json_file(tmp_path):
    lead_file = tmp_path / "lead.json"
    lead_file.write_text(json.dumps(sample_lead()), encoding="utf-8")

    lead = load_lead(lead_file)

    assert lead["lead_id"] == "lead_test"
    assert lead["contact"]["email"] == "ana@example.com"


def test_load_lead_raises_for_missing_file(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Lead file not found"):
        load_lead(missing_file)


def test_validate_lead_raises_for_missing_required_field():
    lead = sample_lead()
    del lead["lead_details"]["message"]

    with pytest.raises(ValueError, match="Lead details are missing required fields"):
        validate_lead(lead)


def test_find_missing_fields_detects_missing_and_blank_values():
    missing_fields = find_missing_fields(
        {"first_name": "Ana", "email": ""},
        ["first_name", "last_name", "email"],
    )

    assert missing_fields == ["last_name", "email"]
