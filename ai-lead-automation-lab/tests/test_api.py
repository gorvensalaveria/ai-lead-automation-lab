from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_page_returns_html_without_openai_call():
    response = client.get("/demo")

    assert response.status_code == 200
    assert "AI Lead Qualification Assistant" in response.text
    assert "Process Lead" in response.text
    assert "Run the AI qualification workflow" in response.text
    assert "data-demo=\"warm\"" in response.text
    assert "sample lead loaded" in response.text
    assert '.replace(/\\n/g, "<br>")' in response.text
    assert "Demo built with Python, FastAPI, OpenAI API" in response.text
    assert "/webhooks/leads" in response.text


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
