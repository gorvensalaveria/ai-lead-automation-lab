# Deployment Guide

This guide describes how to run the AI Lead Intake Automation System outside a local Python environment.

## Required Environment Variables

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-nano
OPENAI_MAX_RETRIES=3
OPENAI_RETRY_BASE_SECONDS=1
OPENAI_TIMEOUT_SECONDS=30
LEAD_PROCESS_RATE_LIMIT_PER_MINUTE=3
LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS=60
APP_ENV=production
WORKFLOW_VERSION=lead-intake-v1
SUMMARY_PROMPT_VERSION=summary-v1
CLASSIFICATION_PROMPT_VERSION=classification-v1
FOLLOW_UP_PROMPT_VERSION=follow-up-v1
```

`OPENAI_API_KEY` is required for AI-powered lead processing. The dashboard, history pages, health check, and static pages can load without making an OpenAI request.

`OPENAI_MAX_RETRIES`, `OPENAI_RETRY_BASE_SECONDS`, and `OPENAI_TIMEOUT_SECONDS` control outbound OpenAI retry and timeout behavior. Transient rate-limit and service errors are retried with exponential backoff plus jitter, while non-retryable API errors fail fast.

`LEAD_PROCESS_RATE_LIMIT_PER_MINUTE` and `LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS` control inbound rate limiting for `POST /webhooks/leads`. This protects public deployments from repeated submissions before expensive OpenAI calls run.

## Health Check

Use this endpoint for deployment health checks:

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

Use this endpoint for detailed operational readiness checks:

```text
GET /health/details
```

It reports output-directory writability, SQLite reachability, configured model, workflow version, saved lead counts, and latest activity.

Every API response includes an `X-Request-ID` header. The API accepts an incoming `X-Request-ID` value and reuses it in structured request logs, which makes webhook calls easier to trace across automation tools.

## Docker

Build the image:

```bash
docker compose build
```

Start the product:

```bash
docker compose up -d
```

Open:

```text
http://127.0.0.1:8000/lead-intake
```

Open the operations status page:

```text
http://127.0.0.1:8000/system-status
```

Stop:

```bash
docker compose down
```

The Compose setup mounts local folders so generated data persists:

- `data/outputs/` stores saved JSON outputs and `lead_intake.db`
- `logs/` stores application logs

## Render

Recommended Render setup:

- Service type: Web Service
- Runtime: Docker
- Dockerfile path: `Dockerfile`
- Health check path: `/health`
- Environment variables:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_MAX_RETRIES`
  - `OPENAI_RETRY_BASE_SECONDS`
  - `OPENAI_TIMEOUT_SECONDS`
  - `LEAD_PROCESS_RATE_LIMIT_PER_MINUTE`
  - `LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS`
  - `APP_ENV=production`
  - `WORKFLOW_VERSION`
  - `SUMMARY_PROMPT_VERSION`
  - `CLASSIFICATION_PROMPT_VERSION`
  - `FOLLOW_UP_PROMPT_VERSION`
  - `GOOGLE_SHEETS_ENABLED=true`
  - `GOOGLE_SHEETS_AUTO_APPEND=true`
  - `GOOGLE_SHEETS_SPREADSHEET_ID`
  - `GOOGLE_SHEETS_RANGE=Leads!A:T`
  - `GOOGLE_SHEETS_VALUE_INPUT_OPTION=RAW`
  - `GOOGLE_SERVICE_ACCOUNT_JSON`

For Render, use `GOOGLE_SERVICE_ACCOUNT_JSON` and paste the full service account JSON as the value. Do not use a local path such as `/Users/your-name/Downloads/service-account.json`, because that file only exists on your computer.

After adding or changing Render environment variables, redeploy the service before testing Google Sheets export.

If using Render without Docker, use:

```bash
uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

For saved lead history to persist across restarts, attach a persistent disk and map it to the application storage path used by `data/outputs/`. Without persistent storage, generated JSON files and the SQLite index may be lost when the service restarts or redeploys.

## Railway

Recommended Railway setup:

- Deploy from the GitHub repository.
- Use the Dockerfile-based deployment if available.
- Add environment variables:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_MAX_RETRIES`
  - `OPENAI_RETRY_BASE_SECONDS`
  - `OPENAI_TIMEOUT_SECONDS`
  - `LEAD_PROCESS_RATE_LIMIT_PER_MINUTE`
  - `LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS`
  - `APP_ENV=production`
  - `WORKFLOW_VERSION`
  - `SUMMARY_PROMPT_VERSION`
  - `CLASSIFICATION_PROMPT_VERSION`
  - `FOLLOW_UP_PROMPT_VERSION`
- Health check path: `/health`

If Railway asks for a start command, use:

```bash
uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

For persistent lead history, configure a Railway volume or move saved lead storage to a managed database.

## Storage Notes

The current production deployment uses:

- JSON files as full audit records
- SQLite as a compact lead history and review-status index
- SQLite audit events as an activity timeline for saved leads
- AI metadata for model, workflow version, prompt versions, and generation timestamps
- CSV export for spreadsheet or CRM handoff
- Google Sheets preview endpoints for handoff-ready rows and append payloads
- Google Sheets live append for manual and automatic spreadsheet export
- Email-based duplicate prevention for Google Sheets handoff, with lead ID as fallback
- System status page and detailed health endpoint for operations readiness
- Privacy-safe masked lead detail views
- Archive workflow that preserves saved audit history
- Bulk review status updates for queue management
- Request IDs and structured JSON request logs for traceability
- OpenAI retry/backoff handling for rate limits and transient API failures
- Inbound lead-processing rate limiting for public endpoint protection

This is appropriate for a single-service production deployment. For hosted multi-user production use, move from local SQLite/files to managed PostgreSQL or another persistent database.

The inbound rate limiter is in-memory and appropriate for one running application instance. For multi-instance production deployments, replace it with Redis or another shared store so limits apply across all instances.

## Integration Notes

The Google Sheets adapter includes preview endpoints, a live append endpoint, and optional automatic append after lead processing. Preview endpoints work without Google credentials:

```text
GET /api/integrations/google-sheets/preview
GET /api/integrations/google-sheets/preview/{saved_output_file_name}.json
```

To enable live Google Sheets writing, add Google Sheets API credentials as deployment secrets, share the target Sheet with the service account, and use:

```text
POST /api/integrations/google-sheets/append/{saved_output_file_name}.json
```

Required environment variables:

```text
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_AUTO_APPEND=true
GOOGLE_SHEETS_SPREADSHEET_ID=your_google_sheet_id_here
GOOGLE_SHEETS_RANGE=Leads!A:T
GOOGLE_SHEETS_VALUE_INPUT_OPTION=RAW
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
```

Use `GOOGLE_SERVICE_ACCOUNT_JSON` instead of `GOOGLE_SERVICE_ACCOUNT_FILE` for hosted deployments that store service account credentials as one secret.

Set `GOOGLE_SHEETS_AUTO_APPEND=true` when every processed webhook lead should be appended automatically after local saving. The app prevents duplicate Google Sheets handoff by checking email first, then lead ID if email is unavailable.

`GOOGLE_SHEETS_VALUE_INPUT_OPTION=RAW` preserves phone numbers and AI-generated text as plain spreadsheet values.

## Privacy Notes

The production system includes privacy-aware controls:

- Detail pages support masked contact data with `?privacy=masked`.
- Archive actions remove a lead from active review queues without deleting the saved audit trail.
- Production deployments should define a retention policy for archived leads and add authenticated hard-delete controls when required by client policy.

## Security Notes

The current deployment keeps reviewer access open unless you add authentication at the platform or application layer.

For deployments with live customer data, add:

- Authentication or API gateway protection
- Role-based access for lead history and detail pages
- Secret management for API keys
- Data retention and deletion controls
- Sensitive-field masking in logs and screenshots

## Deployment Checklist

- Confirm `.env` is not committed.
- Set `OPENAI_API_KEY`.
- Confirm OpenAI retry settings are set or defaults are acceptable.
- Confirm lead-processing rate-limit settings are set or defaults are acceptable.
- Set `APP_ENV=production`.
- Set Google Sheets environment variables when live spreadsheet export is required.
- Confirm `/health` returns `{"status":"ok"}`.
- Confirm `/health` returns an `X-Request-ID` response header.
- Confirm `/health/details` returns storage, SQLite, model, and workflow checks.
- Confirm `/lead-intake` loads.
- Confirm `/system-status` loads.
- Confirm `/api/integrations/google-sheets/preview` returns spreadsheet-ready rows.
- Confirm `POST /api/integrations/google-sheets/append/{saved_output_file_name}.json` appends one test row.
- Confirm clicking **Process Lead** auto-appends to Google Sheets when `GOOGLE_SHEETS_AUTO_APPEND=true`.
- Confirm processing the same email again skips duplicate Google Sheets export.
- Confirm `/history/{saved_output_file_name}.json?privacy=masked` masks email and phone fields.
- Confirm `/api/history/bulk-status` updates selected saved leads in a test environment.
- Confirm `data/outputs/` or the production database persists across restarts.
- Confirm generated `.json`, `.db`, and `.log` files are not committed.
