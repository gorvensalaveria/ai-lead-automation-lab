from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
