import requests

from app.automation.storage import build_result
from app.integrations.hubspot import (
    HUBSPOT_CONTACTS_API_URL,
    HUBSPOT_DELIVERY_FAILED_MESSAGE,
    HUBSPOT_NOT_CONFIGURED_MESSAGE,
    HubSpotConfigError,
    HubSpotDeliveryError,
    build_hubspot_payload,
    build_hubspot_properties,
    send_processed_lead_to_hubspot,
)


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


def sample_processed_result(contact_name: str = "Ana Santos") -> dict:
    result = build_result(
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
    result["crm_ready"]["contact_name"] = contact_name
    return result


def test_hubspot_field_mapping_splits_first_and_last_name():
    properties = build_hubspot_properties(sample_processed_result("Maria Santos"))

    assert properties["firstname"] == "Maria"
    assert properties["lastname"] == "Santos"
    assert properties["email"] == "ana@example.com"
    assert properties["phone"] == "+63 917 555 0123"
    assert properties["company"] == "Santos Software"
    assert properties["lifecyclestage"] == "lead"
    assert properties["hs_lead_status"] == "NEW"
    assert properties["ai_lead_score"] == "100"
    assert properties["ai_classification"] == "hot"
    assert properties["ai_summary"] == "Ana wants lead automation."
    assert properties["ai_follow_up"] == "Hi Ana, thanks for reaching out."
    assert properties["lead_source"] == "website_form"
    assert properties["lead_budget"] == "USD 2,000 - USD 5,000"
    assert properties["lead_timeline"] == "urgent"


def test_hubspot_single_name_omits_lastname():
    properties = build_hubspot_properties(sample_processed_result("Maria"))

    assert properties["firstname"] == "Maria"
    assert "lastname" not in properties


def test_hubspot_payload_shape_is_correct():
    payload = build_hubspot_payload(sample_processed_result())

    assert list(payload) == ["properties"]
    assert payload["properties"]["email"] == "ana@example.com"


def test_hubspot_enabled_but_missing_token_raises_safe_error():
    try:
        send_processed_lead_to_hubspot(
            sample_processed_result(),
            enabled=True,
            access_token="",
        )
    except HubSpotConfigError as error:
        assert str(error) == HUBSPOT_NOT_CONFIGURED_MESSAGE
        assert "token" not in str(error).lower()
    else:
        raise AssertionError("Missing HubSpot token should raise.")


def test_hubspot_enabled_and_configured_sends_one_contact(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "contact_123"}

    def fake_post(url, json, headers, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.integrations.hubspot.requests.post", fake_post)

    result = send_processed_lead_to_hubspot(
        sample_processed_result(),
        enabled=True,
        access_token="hubspot-secret",
        timeout_seconds=7,
    )

    assert result == {"status": "sent", "object_id": "contact_123"}
    assert calls["url"] == HUBSPOT_CONTACTS_API_URL
    assert calls["json"]["properties"]["email"] == "ana@example.com"
    assert calls["headers"]["Authorization"] == "Bearer hubspot-secret"
    assert calls["headers"]["Content-Type"] == "application/json"
    assert calls["timeout"] == 7


def test_hubspot_api_failure_raises_safe_delivery_error(monkeypatch):
    def fake_post(url, json, headers, timeout):
        raise requests.RequestException(
            "401 Unauthorized with Authorization: Bearer hubspot-secret"
        )

    monkeypatch.setattr("app.integrations.hubspot.requests.post", fake_post)

    try:
        send_processed_lead_to_hubspot(
            sample_processed_result(),
            enabled=True,
            access_token="hubspot-secret",
        )
    except HubSpotDeliveryError as error:
        assert str(error) == HUBSPOT_DELIVERY_FAILED_MESSAGE
        assert "hubspot-secret" not in str(error)
        assert "Authorization" not in str(error)
        assert "Traceback" not in str(error)
    else:
        raise AssertionError("HubSpot request failure should raise.")


def test_hubspot_optional_missing_fields_are_omitted_safely():
    result = sample_processed_result("")
    result["crm_ready"]["email"] = None
    result["crm_ready"]["phone"] = None
    result["crm_ready"]["company"] = None
    result["crm_ready"]["lead_score"] = None
    result["crm_ready"]["summary"] = None

    properties = build_hubspot_properties(result)

    assert "firstname" not in properties
    assert "lastname" not in properties
    assert "email" not in properties
    assert "phone" not in properties
    assert "company" not in properties
    assert "ai_lead_score" not in properties
    assert "ai_summary" not in properties
    assert properties["lifecyclestage"] == "lead"
    assert properties["hs_lead_status"] == "NEW"


def test_hubspot_properties_do_not_include_local_output_paths():
    properties = build_hubspot_properties(sample_processed_result())

    assert all("data/outputs" not in str(value) for value in properties.values())
    assert all("/Users/" not in str(value) for value in properties.values())
