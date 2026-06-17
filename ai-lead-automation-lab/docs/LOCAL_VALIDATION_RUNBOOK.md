# Local Validation Runbook

## Purpose

Use this runbook to validate the AI Lead Automation Operating System on a local machine before demos, client review, or production deployment.

The local flow is:

```text
pytest regression tests
-> local server
-> read-only smoke test
-> write smoke test
-> manual UI checks
-> optional integration checks
```

## Prerequisites

- Python 3 installed.
- Project dependencies available from `requirements.txt`.
- A local `.env` file created from `.env.example`.
- OpenAI key available if you plan to process a test lead.
- Optional provider credentials only if you want to test Google Sheets, Airtable, or HubSpot.

## Clean Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Start with local-safe values:

- Keep optional integrations disabled first.
- Keep `WEBHOOK_AUTH_ENABLED=false` if you want browser intake to work without headers locally.
- Add `OPENAI_API_KEY` only to your local `.env`.
- Do not commit `.env`.

## Run Regression Tests

```bash
python3 -m pytest
```

Do not continue to smoke testing until the regression suite passes.

## Start Local Server

```bash
uvicorn app.api:app --reload
```

Expected local base URL:

```text
http://localhost:8000
```

## Read-Only Smoke Test

This checks health, pages, and integration status APIs without submitting a lead:

```bash
python3 scripts/smoke_test.py --base-url http://localhost:8000
```

Expected result:

```text
Smoke test passed: 7/7 checks
```

## Write Smoke Test

This submits a fictional lead and repeats it with the same `Idempotency-Key`.

```bash
python3 scripts/smoke_test.py --base-url http://localhost:8000 --submit-test-lead
```

If webhook API key auth is enabled locally:

```bash
python3 scripts/smoke_test.py --base-url http://localhost:8000 --submit-test-lead --api-key replace_with_local_key
```

Expected result:

- `/webhooks/leads` succeeds.
- Duplicate submission succeeds.
- Output reports whether idempotency appears to work.

## Manual Browser Checks

Open:

- `http://localhost:8000/lead-intake`
- `http://localhost:8000/history`
- `http://localhost:8000/system-status`

Check:

- lead intake page loads,
- saved lead history loads,
- system status page shows integration status,
- recent failed integration runs section loads,
- retry buttons appear only for failed runs.

## Idempotency Check

Run the write smoke test twice with explicit lead submission. The script submits the same request twice in one run using one idempotency key. It should report that the duplicate succeeded and appears idempotent when the app returns the same saved output.

## Optional Local Integration Checks

Enable only one provider at a time during local validation.

Google Sheets:

- Set `GOOGLE_SHEETS_AUTO_APPEND=true`.
- Configure spreadsheet ID, range, and service account credentials.
- Submit a test lead.
- Confirm the row appears in the target sheet.
- Confirm the system status dashboard records success or failure.

Airtable:

- Set `AIRTABLE_ENABLED=true`.
- Configure API key, base ID, and table name.
- Submit a test lead.
- Confirm a record is created or a safe failed run appears.

HubSpot:

- Set `HUBSPOT_ENABLED=true`.
- Configure access token.
- Submit a test lead.
- Confirm a contact is created or a safe failed run appears.

## Security Checks

- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- Webhook auth is enabled before public exposure.
- HMAC is enabled only when the sender can compute the expected signature.
- No real credentials appear in docs, commits, screenshots, or logs.

## Troubleshooting References

- `docs/TROUBLESHOOTING.md`
- `docs/CLIENT_SETUP.md`
- `docs/INTEGRATION_CHECKLIST.md`
- `/system-status`
- terminal logs from the local server
