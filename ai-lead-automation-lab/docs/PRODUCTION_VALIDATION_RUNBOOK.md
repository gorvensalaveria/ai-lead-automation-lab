# Production Validation Runbook

## Purpose

Use this runbook to smoke-test a deployed AI Lead Automation Operating System without adding deployment automation or provider-specific hosting assumptions.

Production validation should happen after regression tests and local smoke tests pass.

## Pre-Deployment Checklist

- Full test suite passes locally.
- `.env` and real credentials are not committed.
- Deployment environment variables are configured in the hosting platform.
- Persistent storage is configured if the host does not keep local files by default.
- Webhook security is enabled.
- Optional integrations are enabled only when credentials are ready.
- Rollback path is known before release.

## Required Production Environment Variables

Minimum:

- `APP_ENV=production`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `WEBHOOK_AUTH_ENABLED=true`
- `WEBHOOK_API_KEYS`

Recommended:

- `WEBHOOK_HMAC_ENABLED=true` when senders can sign requests.
- `WEBHOOK_HMAC_SECRET`
- `WEBHOOK_SIGNATURE_TOLERANCE_SECONDS=300`
- `WEBHOOK_REPLAY_PROTECTION_ENABLED=true`
- `LEAD_PROCESS_RATE_LIMIT_PER_MINUTE`
- `LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS`

Optional integrations:

- Google Sheets variables when spreadsheet dispatch is enabled.
- Airtable variables when Airtable dispatch is enabled.
- HubSpot variables when HubSpot dispatch is enabled.

## Security Recommendations

- Use `WEBHOOK_AUTH_ENABLED=true`.
- Use a strong API key.
- Use optional HMAC for trusted webhook clients that can compute the signature.
- Keep real secrets in the hosting platform secret manager or environment settings.
- Do not store real secrets in the repository.
- Rotate credentials if they are accidentally exposed.

## Storage Warning

This project uses local JSON and SQLite storage. Some hosts erase local disk on redeploy or restart unless persistent disk storage is configured.

Before production use, confirm:

- generated JSON outputs persist,
- SQLite database persists,
- logs are captured by the host or exported,
- backup/retention expectations are clear.

## Read-Only Production Smoke Test

Run this first. It does not submit a lead:

```bash
python3 scripts/smoke_test.py --base-url https://your-production-url
```

Expected checks:

- `/health`
- `/health/details`
- `/system-status`
- `/lead-intake`
- `/history`
- `/api/integrations/status`
- `/api/integrations/runs`

## Explicit Write Smoke Test

Only run this when you are ready to create a fictional test lead in production. It may trigger enabled integrations.

```bash
python3 scripts/smoke_test.py \
  --base-url https://your-production-url \
  --api-key replace_with_production_api_key \
  --submit-test-lead
```

The script prints a warning before submitting to a non-local URL.

Expected behavior:

- first webhook submission succeeds,
- duplicate submission with the same `Idempotency-Key` succeeds,
- script reports whether idempotency appears to work.

## n8n Production Webhook Test

- Configure n8n to send to `https://your-production-url/webhooks/leads`.
- Use `X-API-Key`.
- Use `Idempotency-Key`.
- Keep HMAC disabled unless the workflow computes the required signature.
- Send fictional test lead data.
- Confirm the lead appears in `/history`.

## Make / Zapier Production Request Test

For Make and Zapier:

- Send to `POST /webhooks/leads`.
- Include `Content-Type: application/json`.
- Include `X-API-Key`.
- Include `Idempotency-Key`.
- Use fictional test data.
- Confirm the lead appears in history and the status dashboard updates.

## Google Sheets / Airtable / HubSpot Verification

Google Sheets:

- Confirm expected row appears.
- Confirm duplicate exports are skipped when appropriate.
- Check failed runs on `/system-status`.

Airtable:

- Confirm test record appears.
- Confirm field mapping is acceptable.
- Check failed runs on `/system-status`.

HubSpot:

- Confirm test contact appears.
- Confirm custom properties exist if needed.
- Check failed runs on `/system-status`.

## Rollback Checklist

- Know the previous working deployment version.
- Know how to restore previous environment variables.
- Disable optional integrations if provider failures are noisy.
- Keep webhook auth enabled during rollback.
- Confirm `/health` and `/system-status` after rollback.

## Post-Deploy Demo Checklist

- Open `/lead-intake`.
- Submit a fictional lead only if demo data is acceptable.
- Open `/history`.
- Open a saved lead detail page.
- Open `/system-status`.
- Show integration status and failed-run retry behavior if available.
- Confirm no real credentials appear in the UI, logs, docs, or screenshots.
