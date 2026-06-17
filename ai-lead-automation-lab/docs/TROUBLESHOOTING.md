# Troubleshooting

## App Will Not Start

Check that dependencies are installed and the command is run from the project root:

```bash
python3 -m pip install -r requirements.txt
uvicorn app.api:app --reload
```

If imports fail, confirm the virtual environment is active and Python can see the `app/` package.

## Missing OpenAI Key

Symptom: lead processing fails before an AI result is saved.

Fix:

- Set `OPENAI_API_KEY` in `.env`.
- Confirm `OPENAI_MODEL` is set.
- Restart the app after editing `.env`.

## Invalid API Key

Symptom: `/webhooks/leads` returns `401`.

Fix:

- Confirm `WEBHOOK_AUTH_ENABLED=true`.
- Send `X-API-Key`.
- Make sure the value matches one entry in `WEBHOOK_API_KEYS`.

## Invalid HMAC Signature

Symptom: `/webhooks/leads` returns `401` with invalid signature detail.

Fix:

- Confirm `WEBHOOK_HMAC_SECRET` matches on both sides.
- Sign the exact raw JSON body.
- Use the payload format `"{timestamp}.{raw_body}"`.
- Send signature as `sha256=<hex_digest>`.
- Make sure the timestamp is within `WEBHOOK_SIGNATURE_TOLERANCE_SECONDS`.

## Duplicate Idempotency Key

Symptom: a second request returns the same response as the first request.

This is expected. `Idempotency-Key` is a reliability feature. Reusing the same key prevents duplicate lead processing and duplicate integration dispatch.

Use a new idempotency key for a new lead submission.

## Google Sheets Not Receiving Leads

Check:

- `GOOGLE_SHEETS_AUTO_APPEND=true`.
- Spreadsheet ID and range are set.
- Google Sheets API is enabled.
- The target sheet is shared with the service account email.
- Service account JSON path or JSON environment value is configured.
- The integration status dashboard for failed Google Sheets runs.

Duplicate exports may be skipped by email or lead ID.

## Airtable Not Receiving Leads

Check:

- `AIRTABLE_ENABLED=true`.
- `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, and `AIRTABLE_TABLE_NAME` are set.
- The Airtable token has access to the base.
- The table contains fields expected by the Airtable mapping.
- The integration status dashboard for failed Airtable runs.

The app creates records only. It does not create Airtable fields or upsert existing records.

## HubSpot Not Receiving Leads

Check:

- `HUBSPOT_ENABLED=true`.
- `HUBSPOT_ACCESS_TOKEN` is set.
- The token has permission to create contacts.
- Custom properties such as `ai_lead_score` exist if you want HubSpot to accept them.
- The integration status dashboard for failed HubSpot runs.

The app creates contacts only. It does not search, upsert, create companies, create deals, or create custom properties.

## n8n Webhook Request Fails

Check:

- n8n sends to the FastAPI `/webhooks/leads` endpoint.
- The payload is normalized to the app-compatible lead schema.
- `X-API-Key` is included when auth is enabled.
- `Idempotency-Key` is unique per new lead.
- HMAC is only used if the workflow actually computes the expected signature.

See `integrations/n8n/README.md`.

## Make Scenario Request Fails

Check:

- Make posts to `/webhooks/leads`.
- Headers include `Content-Type`, `X-API-Key`, and `Idempotency-Key`.
- The scenario maps external lead fields into the FastAPI payload shape.
- HMAC is optional advanced security and not required by the starter setup.

See `integrations/make/README.md`.

## Zapier Request Fails

Check:

- Zapier uses Webhooks by Zapier to send a POST or Custom Request.
- Headers include `Content-Type`, `X-API-Key`, and `Idempotency-Key`.
- The payload contains required lead fields.
- The FastAPI app is reachable from Zapier.

See `integrations/zapier/README.md`.

## Integration Retry Fails

Manual retry only works for failed runs. It retries the original provider using the saved lead file.

Check:

- the saved output file still exists,
- the provider is enabled,
- provider credentials are configured,
- the dashboard message after retry,
- server logs for sanitized provider failure context.

Retry does not create a new run row; it updates the existing failed run.

## SQLite / Database Issues

The SQLite database is stored under the output directory. If database checks fail:

- confirm the output directory exists,
- confirm the app can write to it,
- stop any process locking the file,
- restart the app.

The `/system-status` page shows storage and SQLite readiness.

## Tests Failing

Run:

```bash
python3 -m pytest
```

If integration tests fail, confirm they are using mocks and that no real credential is required. If documentation tests fail, check for missing docs, missing README links, placeholder markers, local machine paths, or accidental secret-like strings.

## Where To Look For Logs

Use:

- terminal output from the FastAPI server,
- structured request logs,
- the `logs/` directory if configured locally,
- `/system-status` for runtime readiness and recent integration failures.

Do not paste real API keys, tokens, or service account JSON into issues, logs, demos, or support messages.
