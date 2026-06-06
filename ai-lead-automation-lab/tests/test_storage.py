import json
import pytest

from app.automation.storage import (
    archive_saved_output,
    build_history_csv,
    build_result,
    bulk_update_review_status,
    get_database_path,
    has_exported_email_to_google_sheets,
    has_exported_lead_to_google_sheets,
    has_lead_event,
    list_lead_events,
    list_saved_outputs,
    load_saved_output,
    record_lead_event,
    save_output,
    update_review_status,
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
    assert result["ai_outputs"]["metadata"]["model"]
    assert result["ai_outputs"]["metadata"]["workflow_version"] == "lead-intake-v1"
    assert result["ai_outputs"]["metadata"]["summary_prompt_version"] == "summary-v1"
    assert result["metadata"]["ai"]["classification_prompt_version"] == "classification-v1"
    assert result["crm_ready"]["contact_name"] == "Ana Santos"
    assert result["crm_ready"]["company"] == "Santos Software"
    assert result["crm_ready"]["lead_score"] == 100
    assert result["crm_ready"]["recommended_next_action"].startswith("Reply quickly")
    assert result["crm_ready"]["ai_metadata"]["follow_up_prompt_version"] == "follow-up-v1"


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
    assert get_database_path(tmp_path).exists()


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
    assert history_rows[0]["review_status"] == "new"
    assert history_rows[0]["file_name"].startswith("lead_test_")


def test_build_history_csv_contains_exportable_history_fields(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    save_output(result, output_dir=tmp_path)
    history_rows = list_saved_outputs(output_dir=tmp_path)

    csv_content = build_history_csv(history_rows)

    assert "processed_at,lead_id,contact_name,company,email" in csv_content
    assert "review_status" in csv_content
    assert "Ana Santos" in csv_content
    assert "Santos Software" in csv_content
    assert "hot" in csv_content


def test_update_review_status_persists_to_database_and_json(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    file_path = save_output(result, output_dir=tmp_path)

    row = update_review_status(
        file_name=file_path.name,
        review_status="contacted",
        output_dir=tmp_path,
    )
    saved_result = load_saved_output(file_path.name, output_dir=tmp_path)

    assert row["review_status"] == "contacted"
    assert saved_result["review_status"] == "contacted"
    assert saved_result["crm_ready"]["review_status"] == "contacted"

    events = list_lead_events(file_path.name, output_dir=tmp_path)

    assert events[0]["event_type"] == "review_status_changed"
    assert "contacted" in events[0]["event_detail"]


def test_archive_saved_output_sets_archived_status_and_audit_event(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    file_path = save_output(result, output_dir=tmp_path)

    row = archive_saved_output(file_path.name, output_dir=tmp_path)
    saved_result = load_saved_output(file_path.name, output_dir=tmp_path)
    events = list_lead_events(file_path.name, output_dir=tmp_path)

    assert row["review_status"] == "archived"
    assert saved_result["review_status"] == "archived"
    assert saved_result["crm_ready"]["review_status"] == "archived"
    assert events[0]["event_type"] == "lead_archived"
    assert events[0]["event_label"] == "Lead archived"


def test_bulk_update_review_status_updates_multiple_leads(tmp_path):
    first_result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    second_lead = sample_lead()
    second_lead["lead_id"] = "lead_test_2"
    second_lead["contact"]["first_name"] = "Ben"
    second_result = build_result(
        lead=second_lead,
        summary="Ben wants lead automation.",
        classification="warm",
        score=sample_score(),
        follow_up_message="Hi Ben, thanks for reaching out.",
    )
    first_path = save_output(first_result, output_dir=tmp_path)
    second_path = save_output(second_result, output_dir=tmp_path)

    result = bulk_update_review_status(
        file_names=[first_path.name, second_path.name],
        review_status="reviewed",
        output_dir=tmp_path,
    )

    assert result["requested"] == 2
    assert len(result["updated"]) == 2
    assert result["errors"] == []
    assert all(row["review_status"] == "reviewed" for row in result["updated"])
    assert load_saved_output(first_path.name, output_dir=tmp_path)["review_status"] == "reviewed"
    assert load_saved_output(second_path.name, output_dir=tmp_path)["review_status"] == "reviewed"


def test_bulk_update_review_status_reports_file_errors(tmp_path):
    result = bulk_update_review_status(
        file_names=["missing-output.json"],
        review_status="reviewed",
        output_dir=tmp_path,
    )

    assert result["requested"] == 1
    assert result["updated"] == []
    assert result["errors"][0]["file_name"] == "missing-output.json"


def test_record_lead_event_returns_activity_timeline_rows(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    file_path = save_output(result, output_dir=tmp_path)

    event = record_lead_event(
        file_name=file_path.name,
        event_type="follow_up_copied",
        event_label="Follow-up draft copied",
        event_detail="Reviewer copied the suggested follow-up draft.",
        output_dir=tmp_path,
    )
    events = list_lead_events(file_path.name, output_dir=tmp_path)

    assert event["event_type"] == "follow_up_copied"
    assert events[0]["event_label"] == "Follow-up draft copied"


def test_record_lead_event_accepts_google_sheets_export_event(tmp_path):
    result = build_result(
        lead=sample_lead(),
        summary="Ana wants lead automation.",
        classification="hot",
        score=sample_score(),
        follow_up_message="Hi Ana, thanks for reaching out.",
    )
    file_path = save_output(result, output_dir=tmp_path)

    event = record_lead_event(
        file_name=file_path.name,
        event_type="google_sheets_exported",
        event_label="Google Sheets row appended",
        event_detail="Saved result sent to Google Sheets.",
        output_dir=tmp_path,
    )
    events = list_lead_events(file_path.name, output_dir=tmp_path)

    assert event["event_type"] == "google_sheets_exported"
    assert events[0]["event_label"] == "Google Sheets row appended"
    assert has_lead_event(file_path.name, "google_sheets_exported", output_dir=tmp_path)
    assert has_exported_email_to_google_sheets("ANA@EXAMPLE.COM", output_dir=tmp_path)
    assert has_exported_lead_to_google_sheets("lead_test", output_dir=tmp_path)
    assert any(row["event_type"] == "lead_processed" for row in events)


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
