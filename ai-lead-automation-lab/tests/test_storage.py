import json
import pytest

from app.automation.storage import (
    build_result,
    list_saved_outputs,
    load_saved_output,
    save_output,
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
    assert result["crm_ready"]["contact_name"] == "Ana Santos"
    assert result["crm_ready"]["company"] == "Santos Software"
    assert result["crm_ready"]["lead_score"] == 100
    assert result["crm_ready"]["recommended_next_action"].startswith("Reply quickly")


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
    assert saved_result["crm_ready"]["classification"] == "hot"


def test_list_saved_outputs_returns_history_rows(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    save_output(result, output_dir=tmp_path)

    history_rows = list_saved_outputs(output_dir=tmp_path)

    assert len(history_rows) == 1
    assert history_rows[0]["contact_name"] == "Ana Santos"
    assert history_rows[0]["company"] == "Santos Software"
    assert history_rows[0]["classification"] == "hot"
    assert history_rows[0]["lead_score"] == 100
    assert history_rows[0]["file_name"].startswith("lead_test_")


def test_load_saved_output_returns_saved_result(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    file_path = save_output(result, output_dir=tmp_path)

    saved_result = load_saved_output(file_path.name, output_dir=tmp_path)

    assert saved_result["lead"]["lead_id"] == "lead_test"
    assert saved_result["crm_ready"]["contact_name"] == "Ana Santos"


def test_load_saved_output_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        load_saved_output("../secret.json", output_dir=tmp_path)


def test_load_saved_output_rejects_non_json_file_name(tmp_path):
    with pytest.raises(ValueError):
        load_saved_output("lead_test.txt", output_dir=tmp_path)
