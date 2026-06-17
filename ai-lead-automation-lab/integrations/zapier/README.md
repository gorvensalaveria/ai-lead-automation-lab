# Zapier Lead Intake Workflow

This folder contains Zapier workflow-readiness assets for sending inbound leads into the AI Lead Intake Automation FastAPI backend.

## What The Zap Does

The recommended Zap captures lead data, sends it to FastAPI for AI processing, and optionally routes hot or qualified leads to a notification step.

Zapier sends the lead to FastAPI. FastAPI processes the lead with AI and handles downstream Google Sheets, Airtable, and HubSpot dispatch through the app's integration dispatcher.

Zapier should not directly write to Airtable, HubSpot, or Google Sheets in this milestone.

## Recommended Zap Trigger

Use:

```text
Webhooks by Zapier - Catch Hook
```

Other trigger apps can also work, such as Facebook Lead Ads, Typeform, Google Forms, or a CRM trigger.

## Recommended Zap Actions

1. **Webhooks by Zapier - Custom Request** or **POST**
2. Optional: **Filter by Zapier** for hot or qualified leads
3. Optional: Slack or Email notification placeholder

## Send The Lead To FastAPI

Use:

```text
POST {{LEAD_API_BASE_URL}}/webhooks/leads
```

Headers:

```text
Content-Type: application/json
X-API-Key: {{LEAD_API_KEY}}
Idempotency-Key: {{generated_or_mapped_key}}
```

Map the simple external lead fields into the FastAPI-compatible lead schema in the request body.

## Idempotency

Use an `Idempotency-Key` header for reliable retries.

Good starter options:

- Zapier webhook ID
- source plus email plus submitted timestamp
- another unique lead submission ID

Reuse the same idempotency key if retrying the same lead submission.

## Optional HMAC Security

HMAC is optional and disabled by default locally. API key plus idempotency is the recommended starter setup for Zapier.

If HMAC is enabled, the Zap must compute:

```text
sha256=<hex_digest>
```

from:

```text
"{timestamp}.{raw_body}"
```

Do not claim or assume HMAC works unless the Zap computes the exact expected signature over the exact raw request body sent to FastAPI.

## Test The Zap

1. Start or deploy the FastAPI app.
2. Configure `LEAD_API_BASE_URL`.
3. Configure `LEAD_API_KEY`.
4. Send `sample-webhook-payload.json` to the Catch Hook URL.
5. Confirm Zapier sends the normalized request to FastAPI.
6. Check the FastAPI response, saved output, or history dashboard.

## Intentionally Not Included

This milestone does not include:

- Live Zapier API calls from this repository
- Zapier credentials
- Direct destination sync actions for Google Sheets, Airtable, or HubSpot
- Retry queues
- Background workers
- OAuth flows
- Dashboard UI
- Milestone 7 or later work

For detailed setup steps, see [ZAPIER_SETUP.md](ZAPIER_SETUP.md).
