# Architecture

## Project Purpose

AI Lead Automation Operating System is a FastAPI-based lead intake and automation project. It turns raw lead submissions into AI summaries, classifications, scores, follow-up drafts, saved review records, and optional CRM/spreadsheet handoffs.

## High-Level Diagram

```text
External Form / n8n / Make / Zapier
        ↓
Secure FastAPI Webhook
        ↓
AI Lead Processing
        ↓
Storage: JSON + SQLite
        ↓
Integration Dispatcher
        ↓
Google Sheets / Airtable / HubSpot
        ↓
Integration Runs + Retry Dashboard
```

## Lead Intake Flow

Leads can enter through:

- browser lead intake page,
- local JSON workflow,
- `POST /webhooks/leads`,
- n8n, Make, or Zapier sending a normalized request to FastAPI.

The webhook reads the raw request body first so optional HMAC verification can validate the exact bytes. It then checks idempotency before rate limiting and processing.

## AI Processing Flow

The workflow validates lead fields, then uses the OpenAI API for:

- business need summary,
- hot/warm/cold classification,
- follow-up message generation.

The score is rule-based, using fit, urgency, budget, and intent. The final result includes the original lead, AI outputs, metadata, and CRM-ready flattened fields.

## Storage Flow

Processed leads are saved as JSON files and indexed in SQLite. SQLite stores:

- saved lead history,
- audit events,
- idempotency responses,
- integration run records.

The saved JSON remains the full lead artifact. SQLite supports fast list, status, event, idempotency, and retry queries.

## Integration Dispatcher Flow

After a lead is successfully processed and saved, the dispatcher sends it to enabled destinations:

- Google Sheets,
- Airtable,
- HubSpot.

Disabled providers are skipped and not recorded as integration runs. Destination failures are non-blocking and do not change the public webhook response shape.

## Integration Run Tracking Flow

The dispatcher can record meaningful destination outcomes:

- `success`,
- `failed`,
- `skipped`.

The public run listing exposes safe fields only. Internal `response_json` is stored for retry and diagnostics but is not returned by `GET /api/integrations/runs`.

## Retry Flow

Manual retry is API-only and dashboard-triggered:

1. A failed run is selected.
2. `POST /api/integrations/retry/{run_id}` loads the saved lead by file name.
3. The app retries only the original provider.
4. The existing run is updated.
5. Retry count increments whether the retry succeeds or fails.

There is no background worker, queue, automatic retry scheduler, or retry history table.

## n8n, Make, and Zapier Role

n8n, Make, and Zapier are upstream workflow entry points. They collect or normalize external lead data and send it to FastAPI. They do not directly sync to Google Sheets, Airtable, or HubSpot in this project. FastAPI handles AI processing and downstream dispatch.

## Security Model

API key security:

- `WEBHOOK_AUTH_ENABLED=true` requires `X-API-Key`.
- `WEBHOOK_API_KEYS` stores accepted keys.

Optional HMAC:

- `WEBHOOK_HMAC_ENABLED=true` requires timestamp and signature headers.
- Signature format is `sha256=<hex_digest>`.
- The signed payload is `"{timestamp}.{raw_body}"`.

Idempotency:

- `Idempotency-Key` prevents duplicate webhook processing on client retries.
- Duplicate requests return the original saved successful response.
- Duplicate requests do not reprocess leads or dispatch integrations again.

## Config Model

Configuration is environment-variable based. Local development can keep most integrations disabled. Production-style deployments can enable webhook auth, HMAC, Google Sheets, Airtable, and HubSpot independently.

Integration flags:

- `GOOGLE_SHEETS_AUTO_APPEND`
- `AIRTABLE_ENABLED`
- `HUBSPOT_ENABLED`

## Testing Strategy

The test suite covers:

- lead validation and storage,
- webhook auth and HMAC,
- idempotency,
- Google Sheets, Airtable, and HubSpot handlers with mocks,
- dispatcher behavior,
- n8n/Make/Zapier assets,
- integration run tracking and retry APIs,
- system status dashboard rendering,
- documentation asset checks.

Provider API calls are mocked in tests. No real credentials are required.

## Limitations and Future Improvements

Current limitations:

- manual retry is synchronous,
- no retry queue or background worker,
- no OAuth,
- no HubSpot or Airtable upsert/search-before-create,
- no HubSpot custom-property creation,
- no production admin auth for dashboard endpoints,
- n8n/Make/Zapier assets are starter templates.

Future improvements could include admin auth, queued retries, deployment guides for a hosted environment, OAuth-based CRM setup, richer dashboard filtering, and integration-specific setup validation.
