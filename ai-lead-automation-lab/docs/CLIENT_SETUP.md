# Client Setup Guide

## What This System Does

This project is an AI lead automation system. It receives a lead from a form, browser page, webhook, or automation tool, then:

- summarizes the lead's business need,
- classifies the lead as hot, warm, or cold,
- calculates a lead score,
- drafts a follow-up message,
- saves the result for review,
- sends enabled downstream handoffs to Google Sheets, Airtable, and HubSpot,
- tracks integration runs and allows failed deliveries to be retried manually.

All integrations are optional. The app works locally with only the OpenAI API configured.

## Local Setup

1. Install Python dependencies.

   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. Copy the environment template.

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your own values. Use placeholders until real services are ready.

4. Start the FastAPI app.

   ```bash
   uvicorn app.api:app --reload
   ```

5. Open the browser intake page.

   ```text
   http://127.0.0.1:8000/lead-intake
   ```

## Environment Variables Overview

Core settings:

- `OPENAI_API_KEY`: required for AI summary, classification, and follow-up generation.
- `OPENAI_MODEL`: model used by the AI workflow.
- `APP_ENV`: local environment label.

Webhook security:

- `WEBHOOK_AUTH_ENABLED`: enables API key checks for `/webhooks/leads`.
- `WEBHOOK_API_KEYS`: comma-separated valid API keys.
- `WEBHOOK_HMAC_ENABLED`: enables optional HMAC signature verification.
- `WEBHOOK_HMAC_SECRET`: shared signing secret when HMAC is enabled.
- `WEBHOOK_SIGNATURE_TOLERANCE_SECONDS`: timestamp tolerance for replay protection.
- `WEBHOOK_REPLAY_PROTECTION_ENABLED`: enables timestamp tolerance checking.

Integrations:

- `GOOGLE_SHEETS_ENABLED`
- `GOOGLE_SHEETS_AUTO_APPEND`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_RANGE`
- `GOOGLE_SERVICE_ACCOUNT_FILE` or `GOOGLE_SERVICE_ACCOUNT_JSON`
- `AIRTABLE_ENABLED`
- `AIRTABLE_API_KEY`
- `AIRTABLE_BASE_ID`
- `AIRTABLE_TABLE_NAME`
- `HUBSPOT_ENABLED`
- `HUBSPOT_ACCESS_TOKEN`

Never commit real `.env` values, API keys, service account JSON, access tokens, or private URLs.

## OpenAI Setup

Create an OpenAI API key and set:

```dotenv
OPENAI_API_KEY=replace_with_your_key
OPENAI_MODEL=gpt-5.4-nano
```

If the key is missing or invalid, lead processing will fail before a saved AI result is created.

## Google Sheets Setup

Google Sheets is optional.

1. Create a Google Cloud service account.
2. Enable the Google Sheets API.
3. Share the target spreadsheet with the service account email.
4. Set the spreadsheet ID and credentials in `.env`.
5. Set `GOOGLE_SHEETS_AUTO_APPEND=true` if webhook-processed leads should be sent automatically.

Google Sheets duplicate export protection checks email first, then lead ID.

## Airtable Setup

Airtable is optional.

1. Create an Airtable base and table.
2. Create an API token with access to that base.
3. Set:

```dotenv
AIRTABLE_ENABLED=true
AIRTABLE_API_KEY=replace_with_airtable_token
AIRTABLE_BASE_ID=replace_with_base_id
AIRTABLE_TABLE_NAME=Leads
```

The app creates one Airtable record per processed lead. It does not create Airtable fields, detect duplicates, or upsert records.

## HubSpot Setup

HubSpot is optional.

1. Create a HubSpot private app access token.
2. Set:

```dotenv
HUBSPOT_ENABLED=true
HUBSPOT_ACCESS_TOKEN=replace_with_hubspot_token
```

The app creates one HubSpot contact per processed lead. It does not search before create, upsert, create companies, create deals, or create custom properties.

## Webhook Auth Setup

For production-style use:

```dotenv
WEBHOOK_AUTH_ENABLED=true
WEBHOOK_API_KEYS=replace_with_strong_key
```

Send the key with:

```text
X-API-Key: replace_with_strong_key
```

Optional HMAC security can also be enabled. HMAC uses:

```text
X-Webhook-Timestamp
X-Webhook-Signature
```

The signature format is `sha256=<hex_digest>` over `"{timestamp}.{raw_body}"`.

Use `Idempotency-Key` on webhook requests to avoid duplicate processing when a client retries the same submission.

## n8n, Make, and Zapier Setup References

These tools send leads into FastAPI. FastAPI owns AI processing and downstream dispatch to Google Sheets, Airtable, and HubSpot.

- n8n: `integrations/n8n/README.md`
- Make: `integrations/make/README.md`
- Zapier: `integrations/zapier/README.md`

## Submit a Sample Lead

Use the browser page:

```text
http://127.0.0.1:8000/lead-intake
```

Or post JSON to:

```text
POST /webhooks/leads
```

Include `X-API-Key` when webhook auth is enabled. Include `Idempotency-Key` for safe retries.

## View History

Open:

```text
http://127.0.0.1:8000/history
```

The history dashboard shows saved leads, review status, filters, CSV export, and detail links.

## Check Integration Status

Open:

```text
http://127.0.0.1:8000/system-status
```

The Integration Status section shows enabled providers, success counts, failed counts, and recent failed runs.

## Retry Failed Integration Runs

On `/system-status`, use the Retry button beside a failed integration run. The app retries only the original provider and refreshes the status table afterward.

The API endpoint is:

```text
POST /api/integrations/retry/{run_id}
```

Only failed runs can be retried.
