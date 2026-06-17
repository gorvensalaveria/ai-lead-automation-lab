# Integration Checklist

Use this before a demo, client handoff, or technical review.

## Local App

- [ ] Dependencies are installed.
- [ ] `.env` exists locally.
- [ ] FastAPI starts with `uvicorn app.api:app --reload`.
- [ ] `/lead-intake` opens.
- [ ] `/history` opens.
- [ ] `/system-status` opens.

## .env Safety

- [ ] `.env` is not committed.
- [ ] Real API keys are not in docs, screenshots, or logs.
- [ ] Service account JSON is not committed.
- [ ] Placeholder values are used in shared examples.

## OpenAI

- [ ] `OPENAI_API_KEY` is set locally.
- [ ] `OPENAI_MODEL` is set.
- [ ] A sample lead can be processed.
- [ ] AI summary, classification, score, and follow-up appear.

## Google Sheets

- [ ] `GOOGLE_SHEETS_AUTO_APPEND` is intentionally set.
- [ ] Spreadsheet ID is configured if enabled.
- [ ] Range is configured.
- [ ] Service account credentials are configured.
- [ ] Target sheet is shared with the service account.
- [ ] Dashboard shows Google Sheets status.

## Airtable

- [ ] `AIRTABLE_ENABLED` is intentionally set.
- [ ] API token is configured if enabled.
- [ ] Base ID is configured.
- [ ] Table name is configured.
- [ ] Expected fields exist in Airtable.
- [ ] Dashboard shows Airtable status.

## HubSpot

- [ ] `HUBSPOT_ENABLED` is intentionally set.
- [ ] Private app access token is configured if enabled.
- [ ] Contact create permission is available.
- [ ] Custom properties exist if the portal should accept AI fields.
- [ ] Dashboard shows HubSpot status.

## n8n

- [ ] n8n README reviewed.
- [ ] Workflow starter imported or recreated.
- [ ] Lead payload is normalized before sending to FastAPI.
- [ ] `X-API-Key` is configured when auth is enabled.
- [ ] `Idempotency-Key` is configured.

## Make

- [ ] Make README reviewed.
- [ ] Starter blueprint recreated or adjusted.
- [ ] Lead payload is normalized before sending to FastAPI.
- [ ] `X-API-Key` is configured when auth is enabled.
- [ ] `Idempotency-Key` is configured.

## Zapier

- [ ] Zapier setup guide reviewed.
- [ ] Catch Hook or equivalent trigger is configured.
- [ ] Webhook POST/Custom Request sends to FastAPI.
- [ ] `X-API-Key` is configured when auth is enabled.
- [ ] `Idempotency-Key` is configured.

## Webhook Security

- [ ] `WEBHOOK_AUTH_ENABLED` is set appropriately.
- [ ] `WEBHOOK_API_KEYS` uses strong values outside local demos.
- [ ] HMAC is enabled only when the sender computes the correct signature.
- [ ] `Idempotency-Key` is sent for retry-prone clients.

## Integration Status Dashboard

- [ ] `/system-status` shows Integration Status.
- [ ] Failed runs appear in Recent Failed Integration Runs.
- [ ] Retry button is visible only for failed runs.
- [ ] Retry refreshes provider status and failed run list.

## Tests

- [ ] Documentation tests pass.
- [ ] Full test suite passes.

```bash
python3 -m pytest tests/test_documentation_assets.py
python3 -m pytest
```
