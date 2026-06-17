#!/usr/bin/env python3
"""Smoke-test a local or deployed AI Lead Automation app."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


READ_ONLY_ENDPOINTS = [
    ("GET", "/health"),
    ("GET", "/health/details"),
    ("GET", "/system-status"),
    ("GET", "/lead-intake"),
    ("GET", "/history"),
    ("GET", "/api/integrations/status"),
    ("GET", "/api/integrations/runs"),
]

SAMPLE_LEAD = {
    "lead_id": "smoke_test_lead",
    "name": "Test Lead",
    "source": "Smoke Test",
    "submitted_at": "2026-06-16T00:00:00+00:00",
    "business_type": "Test",
    "contact": {
        "first_name": "Test",
        "last_name": "Lead",
        "email": "test.lead@example.com",
        "phone": "+639000000000",
        "company": "Demo Company",
    },
    "lead_details": {
        "service_interest": "AI automation validation",
        "message": "This is a smoke test lead.",
        "budget_range": "Test Budget",
        "timeline": "Test Timeline",
        "preferred_contact_method": "email",
        "pain_point": "Testing webhook intake.",
        "industry": "Test",
    },
}


@dataclass
class CheckResult:
    """One smoke test check result."""

    label: str
    passed: bool
    detail: str = ""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run local or production smoke checks against the AI Lead Automation app.",
    )
    parser.add_argument("--base-url", required=True, help="Base URL, such as http://localhost:8000.")
    parser.add_argument("--api-key", default="", help="Optional webhook API key for test lead submission.")
    parser.add_argument(
        "--submit-test-lead",
        action="store_true",
        help="Submit a fictional test lead and repeat it with the same Idempotency-Key.",
    )
    parser.add_argument("--timeout", type=float, default=10, help="HTTP timeout in seconds.")
    parser.add_argument("--verbose", action="store_true", help="Print short response snippets.")
    return parser.parse_args()


def main() -> int:
    """Run smoke checks and return an exit code."""
    args = parse_args()
    base_url = normalize_base_url(args.base_url)
    results: list[CheckResult] = []

    for method, path in READ_ONLY_ENDPOINTS:
        results.append(check_endpoint(base_url, method, path, timeout=args.timeout, verbose=args.verbose))

    if args.submit_test_lead:
        if not is_local_url(base_url):
            print("WARNING: submitting a test lead to a non-local URL may create production data and trigger enabled integrations.")
        results.append(
            check_webhook_submission(
                base_url=base_url,
                api_key=args.api_key,
                timeout=args.timeout,
                verbose=args.verbose,
            )
        )

    passed = sum(1 for result in results if result.passed)
    total = len(results)

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        suffix = f" - {result.detail}" if result.detail else ""
        print(f"{status} {result.label}{suffix}")

    if passed == total:
        print(f"Smoke test passed: {passed}/{total} checks")
        return 0

    print(f"Smoke test failed: {passed}/{total} checks passed")
    return 1


def normalize_base_url(base_url: str) -> str:
    """Return a base URL with one trailing slash."""
    return base_url.rstrip("/") + "/"


def check_endpoint(
    base_url: str,
    method: str,
    path: str,
    *,
    timeout: float,
    verbose: bool,
) -> CheckResult:
    """Check one read-only endpoint."""
    response = make_request(
        method=method,
        url=urljoin(base_url, path.lstrip("/")),
        timeout=timeout,
    )
    label = path
    if response["ok"]:
        detail = response_snippet(response, verbose)
        return CheckResult(label=label, passed=True, detail=detail)

    return CheckResult(
        label=label,
        passed=False,
        detail=f"{response['status']} {response['error']}".strip(),
    )


def check_webhook_submission(
    *,
    base_url: str,
    api_key: str,
    timeout: float,
    verbose: bool,
) -> CheckResult:
    """Submit one fictional lead twice with the same idempotency key."""
    idempotency_key = f"smoke-test-{uuid.uuid4()}"
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    if api_key:
        headers["X-API-Key"] = api_key

    url = urljoin(base_url, "webhooks/leads")
    body = json.dumps(SAMPLE_LEAD).encode("utf-8")
    first = make_request(method="POST", url=url, body=body, headers=headers, timeout=timeout)
    second = make_request(method="POST", url=url, body=body, headers=headers, timeout=timeout)
    label = "/webhooks/leads idempotency"

    if not first["ok"]:
        return CheckResult(label=label, passed=False, detail=f"first submit failed: {first['status']} {first['error']}".strip())
    if not second["ok"]:
        return CheckResult(label=label, passed=False, detail=f"duplicate submit failed: {second['status']} {second['error']}".strip())

    first_json = parse_json_response(first.get("body", ""))
    second_json = parse_json_response(second.get("body", ""))
    appears_idempotent = duplicate_appears_idempotent(first_json, second_json)
    detail = "duplicate appears idempotent" if appears_idempotent else "duplicate succeeded; idempotency could not be confirmed"
    snippet = response_snippet(second, verbose)
    if snippet:
        detail = f"{detail}; {snippet}"

    return CheckResult(label=label, passed=True, detail=detail)


def make_request(
    *,
    method: str,
    url: str,
    timeout: float,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Make an HTTP request with urllib and return a compact result."""
    request = Request(
        url,
        data=body,
        method=method,
        headers=headers or {},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "body": response_body,
                "error": "",
            }
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": error.code,
            "body": error_body,
            "error": error.reason or error_body[:120],
        }
    except URLError as error:
        return {
            "ok": False,
            "status": "",
            "body": "",
            "error": str(error.reason),
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": "",
            "body": "",
            "error": "request timed out",
        }


def response_snippet(response: dict[str, Any], verbose: bool) -> str:
    """Return a short response snippet when verbose mode is enabled."""
    if not verbose:
        return ""

    body = str(response.get("body", "")).replace("\n", " ").strip()
    return body[:160]


def parse_json_response(body: str) -> dict[str, Any]:
    """Parse a JSON response body, returning an empty dict on failure."""
    try:
        value = json.loads(body)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def duplicate_appears_idempotent(first: dict[str, Any], second: dict[str, Any]) -> bool:
    """Best-effort idempotency signal without requiring full JSON equality."""
    if not first or not second:
        return False

    if first == second:
        return True

    first_output = first.get("output_path")
    second_output = second.get("output_path")
    if first_output and first_output == second_output:
        return True

    first_lead_id = first.get("result", {}).get("lead", {}).get("lead_id")
    second_lead_id = second.get("result", {}).get("lead", {}).get("lead_id")
    return bool(first_lead_id and first_lead_id == second_lead_id)


def is_local_url(base_url: str) -> bool:
    """Return whether a base URL points to a local development host."""
    host = urlparse(base_url).hostname or ""
    return host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


if __name__ == "__main__":
    sys.exit(main())
