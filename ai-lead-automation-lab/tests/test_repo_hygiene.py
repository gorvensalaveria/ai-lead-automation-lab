from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ENV_EXAMPLE = ROOT / ".env.example"
GITIGNORE = ROOT / ".gitignore"
DOCS_DIR = ROOT / "docs"

REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".env.*",
    "!.env.example",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "data/outputs/*.json",
    "data/outputs/*.db",
    "data/outputs/*.sqlite",
    "data/outputs/*.sqlite3",
    "logs/*.log",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    ".DS_Store",
    "__MACOSX/",
    "node_modules/",
]

HANDOFF_DOC_LINKS = [
    "docs/CLIENT_SETUP.md",
    "docs/ARCHITECTURE.md",
    "docs/TROUBLESHOOTING.md",
    "docs/DEMO_SCRIPT.md",
    "docs/PORTFOLIO_CASE_STUDY.md",
    "docs/INTEGRATION_CHECKLIST.md",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"pat_[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_contains_final_project_positioning_and_docs():
    readme = read(README)

    assert "AI Lead Automation Operating System" in readme
    assert "A production-style AI lead automation system" in readme
    for link in HANDOFF_DOC_LINKS:
        assert link in readme


def test_gitignore_includes_required_secret_and_generated_patterns():
    lines = {
        line.strip()
        for line in read(GITIGNORE).splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        assert pattern in lines


def test_env_example_exists_and_uses_safe_placeholders():
    assert ENV_EXAMPLE.exists()
    content = read(ENV_EXAMPLE)

    assert "/Users/" not in content
    assert "replace_with_openai_api_key" in content
    assert "replace_with_strong_webhook_key" in content
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(content)


def test_docs_do_not_contain_todo_or_full_local_paths():
    for path in DOCS_DIR.glob("*.md"):
        content = read(path)
        assert "TODO" not in content
        assert "/Users/" not in content
