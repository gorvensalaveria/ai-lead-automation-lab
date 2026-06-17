import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "smoke_test.py"
LOCAL_RUNBOOK = ROOT / "docs" / "LOCAL_VALIDATION_RUNBOOK.md"
PRODUCTION_RUNBOOK = ROOT / "docs" / "PRODUCTION_VALIDATION_RUNBOOK.md"
README = ROOT / "README.md"

REQUIRED_FLAGS = [
    "--base-url",
    "--api-key",
    "--submit-test-lead",
    "--timeout",
    "--verbose",
]

REQUIRED_ENDPOINTS = [
    "/health",
    "/health/details",
    "/system-status",
    "/lead-intake",
    "/history",
    "/api/integrations/status",
    "/api/integrations/runs",
    "/webhooks/leads",
]

BLOCKED_PATTERNS = [
    "sk-",
    "pat_",
    "xoxb-",
    "BEGIN PRIVATE KEY",
    "Authorization: Bearer",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_smoke_script_exists():
    assert SCRIPT.exists()


def test_smoke_script_cli_help_works_without_server():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in REQUIRED_FLAGS:
        assert flag in result.stdout


def test_smoke_script_contains_required_endpoint_checks():
    content = read(SCRIPT)

    for endpoint in REQUIRED_ENDPOINTS:
        assert endpoint in content


def test_smoke_script_uses_safe_fictional_test_data():
    content = read(SCRIPT)

    assert "Test Lead" in content
    assert "test.lead@example.com" in content
    assert "+639000000000" in content
    assert "Demo Company" in content
    for pattern in BLOCKED_PATTERNS:
        assert pattern not in content


def test_validation_runbooks_exist_and_readme_links_to_them():
    assert LOCAL_RUNBOOK.exists()
    assert PRODUCTION_RUNBOOK.exists()

    readme = read(README)
    assert "docs/LOCAL_VALIDATION_RUNBOOK.md" in readme
    assert "docs/PRODUCTION_VALIDATION_RUNBOOK.md" in readme
