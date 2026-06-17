import json
import re
from pathlib import Path


N8N_DIR = Path("integrations/n8n")
README_PATH = N8N_DIR / "README.md"
WORKFLOW_PATH = N8N_DIR / "lead-intake-ai-automation.workflow.json"
SAMPLE_PAYLOAD_PATH = N8N_DIR / "sample-webhook-payload.json"
SECURE_HEADERS_PATH = N8N_DIR / "sample-secure-headers.md"


def test_n8n_asset_files_exist():
    assert README_PATH.exists()
    assert WORKFLOW_PATH.exists()
    assert SAMPLE_PAYLOAD_PATH.exists()
    assert SECURE_HEADERS_PATH.exists()


def test_n8n_workflow_json_is_valid():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))

    assert workflow["name"]
    assert isinstance(workflow["nodes"], list)
    assert workflow["nodes"]


def test_n8n_workflow_contains_webhook_and_http_request_nodes():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = workflow["nodes"]
    node_names = {node.get("name", "") for node in nodes}
    node_types = {node.get("type", "") for node in nodes}

    assert "Lead Intake Webhook" in node_names
    assert "n8n-nodes-base.webhook" in node_types
    assert "Send Lead to FastAPI" in node_names
    assert "n8n-nodes-base.httpRequest" in node_types


def test_n8n_workflow_references_fastapi_webhook_and_security_headers():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "/webhooks/leads" in workflow_text
    assert "X-API-Key" in workflow_text
    assert "Idempotency-Key" in workflow_text
    assert "LEAD_API_BASE_URL" in workflow_text
    assert "LEAD_API_KEY" in workflow_text


def test_n8n_sample_payload_is_valid_and_contains_required_fields():
    payload = json.loads(SAMPLE_PAYLOAD_PATH.read_text(encoding="utf-8"))

    assert payload["name"]
    assert payload["email"]
    assert payload["company"]
    assert payload["source"]
    assert payload.get("message") or payload.get("pain_point")


def test_n8n_docs_explain_fastapi_dispatch_ownership():
    readme_text = README_PATH.read_text(encoding="utf-8")

    assert "n8n sends the lead to FastAPI" in readme_text
    assert "FastAPI processes the lead" in readme_text
    assert "integration dispatcher" in readme_text
    assert "does not directly append to Google Sheets or Airtable" in readme_text


def test_n8n_secure_headers_doc_explains_hmac_format():
    headers_text = SECURE_HEADERS_PATH.read_text(encoding="utf-8")

    assert "X-API-Key" in headers_text
    assert "Idempotency-Key" in headers_text
    assert "X-Webhook-Timestamp" in headers_text
    assert "X-Webhook-Signature" in headers_text
    assert '"{timestamp}.{raw_body}"' in headers_text
    assert "sha256=<hex_digest>" in headers_text
    assert "disabled by default locally" in headers_text


def test_n8n_assets_do_not_contain_obvious_real_secrets():
    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            README_PATH,
            WORKFLOW_PATH,
            SAMPLE_PAYLOAD_PATH,
            SECURE_HEADERS_PATH,
        ]
    )
    obvious_secret_patterns = [
        r"sk-[A-Za-z0-9_-]{20,}",
        r"pat[A-Za-z0-9]{20,}",
        r"key[A-Za-z0-9]{20,}",
        r"Bearer\s+[A-Za-z0-9._-]{20,}",
        r"https://[^\\s\"']*(?:ngrok|trycloudflare|localhost\\.run)[^\\s\"']*",
    ]

    for pattern in obvious_secret_patterns:
        assert re.search(pattern, combined_text) is None
