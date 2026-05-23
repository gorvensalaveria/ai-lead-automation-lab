import json

from app.automation.storage import build_result, save_output


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


def test_build_result_contains_expected_output_sections():
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )

    assert "processed_at" in result
    assert result["lead"]["lead_id"] == "lead_test"
    assert result["ai_outputs"]["summary"] == "Ana wants lead automation."
    assert result["ai_outputs"]["classification"] == "hot"
    assert result["ai_outputs"]["score"]["rating"] == "high"
    assert result["ai_outputs"]["follow_up_message"].startswith("Hi Ana")


def test_save_output_writes_result_to_json_file(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )

    file_path = save_output(result, output_dir=tmp_path)

    assert file_path.exists()
    assert file_path.name.startswith("lead_test_")
    assert file_path.suffix == ".json"

    saved_result = json.loads(file_path.read_text(encoding="utf-8"))
    assert saved_result["lead"]["lead_id"] == "lead_test"
    assert saved_result["ai_outputs"]["classification"] == "hot"
