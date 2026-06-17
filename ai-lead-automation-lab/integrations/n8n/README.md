# n8n Lead Intake Workflow

This folder contains an n8n starter workflow for sending inbound leads into the AI Lead Intake Automation FastAPI backend.

The workflow is designed as an import-ready starter template. Depending on your n8n version, you may need to adjust node versions or credentials after import.

## What The Workflow Does

The workflow demonstrates this business flow:

1. Receive a lead through an n8n Webhook trigger.
2. Normalize the simple incoming lead payload into the FastAPI app's `/webhooks/leads` schema.
3. Generate an `Idempotency-Key` for reliable retries.
4. Send the normalized lead to `POST /webhooks/leads`.
5. Check the AI classification and lead score from the FastAPI response.
6. Route hot or qualified leads to a sales notification placeholder.
7. Keep Google Sheets and Airtable delivery inside the FastAPI app's integration dispatcher.
8. Provide a simple error branch placeholder for failed API requests.

The n8n workflow does not directly send to Airtable or Google Sheets in this milestone. n8n sends the lead to FastAPI. FastAPI processes the lead and handles downstream Google Sheets/Airtable dispatch through the app's integration dispatcher.

## Files

- `lead-intake-ai-automation.workflow.json` - n8n starter workflow JSON.
- `sample-webhook-payload.json` - simple external lead payload for testing the n8n webhook.
- `sample-secure-headers.md` - secure header reference for the FastAPI webhook.

## Required n8n Environment Variables

Set these in your n8n environment:

```text
LEAD_API_BASE_URL=http://127.0.0.1:8000
LEAD_API_KEY=local-dev-key
```

For production, use the deployed HTTPS base URL for `LEAD_API_BASE_URL` and a strong API key configured in the FastAPI app.

## Import The Workflow

1. Open n8n.
2. Go to **Workflows**.
3. Choose **Import from File**.
4. Select `integrations/n8n/lead-intake-ai-automation.workflow.json`.
5. Review the imported nodes.
6. Confirm the HTTP Request node points to:

```text
{{ $env.LEAD_API_BASE_URL }}/webhooks/leads
```

7. Configure your n8n environment variables.
8. Save and activate the workflow when ready.

## Test The Workflow

Start the FastAPI app locally:

```bash
uvicorn app.api:app --reload
```

If webhook auth is enabled in FastAPI, make sure the app has:

```text
WEBHOOK_AUTH_ENABLED=true
WEBHOOK_API_KEYS=local-dev-key
```

In n8n, open the Webhook trigger test URL and send `sample-webhook-payload.json`.

The workflow normalizes that simple payload into the app-compatible payload before calling FastAPI.

## Idempotency

The workflow includes a generated `Idempotency-Key` header when calling FastAPI.

This helps prevent duplicate processing if n8n retries a request or if the same lead submission is sent twice. The FastAPI app stores successful responses for idempotency keys and returns the original response for duplicate keys.

## Google Sheets And Airtable Dispatch

The workflow does not directly append to Google Sheets or Airtable.

FastAPI handles downstream dispatch after AI processing:

- Google Sheets dispatch is controlled by `GOOGLE_SHEETS_AUTO_APPEND`.
- Airtable dispatch is controlled by `AIRTABLE_ENABLED`.
- Both destinations are managed by the app's integration dispatcher.

This keeps n8n focused on intake and orchestration while the backend owns processing, storage, and destination delivery.

## Optional HMAC Security

HMAC is optional and disabled by default locally.

The starter workflow uses:

- `X-API-Key`
- `Idempotency-Key`

If HMAC is enabled in FastAPI, add:

- `X-Webhook-Timestamp`
- `X-Webhook-Signature`

The HMAC payload format is:

```text
"{timestamp}.{raw_body}"
```

The signature format is:

```text
sha256=<hex_digest>
```

Do not enable HMAC in this n8n workflow unless your n8n expression or custom code node computes the exact signature expected by FastAPI.

## Error Handling

The starter workflow includes an error branch placeholder for failed API requests.

Recommended production behavior:

- Log the failed request.
- Notify an operator or sales operations channel.
- Do not expose secrets in notifications.
- Retry only when you understand whether the request is safe to repeat.
- Reuse the same `Idempotency-Key` for safe retries of the same lead.

## Intentionally Not Included

This milestone does not include:

- Direct Airtable writes from n8n
- Direct Google Sheets writes from n8n
- HubSpot integration
- Make integration
- Zapier integration
- Retry queues
- Background workers
- OAuth flows
- Real n8n credentials
- Real API keys or private URLs
