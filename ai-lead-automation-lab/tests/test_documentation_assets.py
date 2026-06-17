from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REQUIRED_DOCS = [
    ROOT / "docs" / "CLIENT_SETUP.md",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "TROUBLESHOOTING.md",
    ROOT / "docs" / "DEMO_SCRIPT.md",
    ROOT / "docs" / "PORTFOLIO_CASE_STUDY.md",
    ROOT / "docs" / "INTEGRATION_CHECKLIST.md",
]
CORE_INTEGRATIONS = [
    "Google Sheets",
    "Airtable",
    "HubSpot",
    "n8n",
    "Make",
    "Zapier",
]
SECURITY_TERMS = [
    "API key",
    "HMAC",
    "idempotency",
]
BLOCKED_PATTERNS = [
    "/Users/",
    "sk-",
    "pat_",
    "xoxb-",
    "Authorization: Bearer ",
    "BEGIN PRIVATE KEY",
    "TODO",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_documentation_files_exist():
    for path in REQUIRED_DOCS:
        assert path.exists(), f"Missing documentation file: {path.name}"
        assert path.stat().st_size > 500, f"Documentation file is too shallow: {path.name}"


def test_readme_links_to_required_documentation():
    readme = read(README)

    for path in REQUIRED_DOCS:
        relative_path = path.relative_to(ROOT).as_posix()
        assert relative_path in readme


def test_docs_mention_core_integrations():
    combined_docs = "\n".join(read(path) for path in REQUIRED_DOCS)

    for integration in CORE_INTEGRATIONS:
        assert integration in combined_docs


def test_docs_mention_security_terms():
    combined_docs = "\n".join(read(path) for path in REQUIRED_DOCS)
    normalized_docs = combined_docs.lower()

    for term in SECURITY_TERMS:
        assert term.lower() in normalized_docs


def test_docs_do_not_contain_obvious_secrets_or_local_paths():
    combined_docs = "\n".join(read(path) for path in REQUIRED_DOCS)

    for pattern in BLOCKED_PATTERNS:
        assert pattern not in combined_docs
