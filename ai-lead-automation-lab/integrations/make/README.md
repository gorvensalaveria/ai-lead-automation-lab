# Make Lead Intake Scenario

This folder contains Make.com workflow-readiness assets for sending inbound leads into the AI Lead Intake Automation FastAPI backend.

This blueprint is a documented starter blueprint, not guaranteed to be directly importable into every Make workspace. Recreate or adjust modules in Make if import compatibility differs.

## What The Scenario Does

The scenario demonstrates this flow:

1. Receive a lead through a Make Custom Webhook.
2. Normalize the simple incoming lead payload into the FastAPI app's `/webhooks/leads` schema.
3. Generate or map an `Idempotency-Key`.
4. Send the normalized lead to `POST /webhooks/leads`.
5. Route hot or qualified leads through a Make router.
6. Send a notification placeholder for qualified leads.
7. Use an error handling route placeholder for failed API requests.

Make sends the lead to FastAPI. FastAPI processes the lead with AI and handles downstream Google Sheets, Airtable, and HubSpot dispatch through the app's integration dispatcher.

Make should not directly write to Airtable, HubSpot, or Google Sheets in this milestone.

## Files

- `lead-intake-ai-automation.blueprint.json` - documented starter pseudo-blueprint.
- `sample-webhook-payload.json` - simple external lead payload for testing.
- `sample-secure-headers.md` - secure header reference for Make HTTP requests.

## Required Make Modules

- **Webhooks > Custom webhook**
- **Tools > Set variable** or mapping step for normalization
- **HTTP > Make a request**
- **Router** for hot/qualified vs normal leads
- Notification placeholder such as Slack, Email, or another internal Make module
- Error handler route placeholder

## Required Configuration Values

Use Make variables, data store values, or manually configured placeholders:

```text
LEAD_API_BASE_URL=https://your-fastapi-app.example.com
LEAD_API_KEY=replace-with-your-configured-api-key
```

For local testing, use a deployed URL or secure tunnel. Make cloud cannot normally reach `127.0.0.1` on your computer.

## Create The Custom Webhook Trigger

1. In Make, create a new scenario.
2. Add **Webhooks > Custom webhook**.
3. Create a new webhook.
4. Copy the Make webhook URL.
5. Send `sample-webhook-payload.json` to the webhook URL to capture the data structure.

## Add The HTTP Request To FastAPI

Add **HTTP > Make a request**.

Use:

```text
POST {{LEAD_API_BASE_URL}}/webhooks/leads
```

Body type:

```text
Raw JSON
```

Headers:

```text
Content-Type: application/json
X-API-Key: {{LEAD_API_KEY}}
Idempotency-Key: {{generated_or_mapped_key}}
```

Map the simple external lead payload into the FastAPI-compatible schema:

```json
{
  "lead_id": "make_{{generated_or_mapped_key}}",
  "source": "{{source}}",
  "submitted_at": "{{now}}",
  "business_type": "{{industry}}",
  "contact": {
    "first_name": "{{first_name}}",
    "last_name": "{{last_name}}",
    "email": "{{email}}",
    "phone": "{{phone}}",
    "company": "{{company}}"
  },
  "lead_details": {
    "service_interest": "{{pain_point}}",
    "message": "{{message}}",
    "budget_range": "{{budget}}",
    "timeline": "{{timeline}}",
    "preferred_contact_method": "email"
  }
}
```

## Idempotency

Use an `Idempotency-Key` header for reliability. A good starter key can be derived from the source, email, and Make bundle ID.

Reuse the same idempotency key when retrying the same lead. FastAPI returns the original successful response and avoids duplicate processing for repeated keys.

## Routing Qualified Leads

After the HTTP module, add a Router or filter branch.

Example qualified condition:

```text
classification equals hot
OR
lead score greater than or equal to 75
```

The FastAPI response includes AI classification and score in the processed result.

## Google Sheets, Airtable, And HubSpot Dispatch

FastAPI owns downstream dispatch:

- Google Sheets dispatch is controlled by `GOOGLE_SHEETS_AUTO_APPEND`.
- Airtable dispatch is controlled by `AIRTABLE_ENABLED`.
- HubSpot dispatch is controlled by `HUBSPOT_ENABLED`.

Make should not directly sync to those destinations in this milestone.

## Optional HMAC Security

HMAC is optional and disabled by default locally.

The recommended starter setup for Make is:

- `X-API-Key`
- `Idempotency-Key`

If HMAC is enabled, Make must compute:

```text
sha256=<hex_digest>
```

from:

```text
"{timestamp}.{raw_body}"
```

Do not enable HMAC in Make unless your scenario computes the exact signature expected by FastAPI.

## Test The Scenario

1. Start or deploy the FastAPI app.
2. Configure `LEAD_API_BASE_URL`.
3. Configure `LEAD_API_KEY`.
4. Send `sample-webhook-payload.json` to the Make Custom Webhook.
5. Confirm the HTTP module receives a successful response from FastAPI.
6. Check the FastAPI history dashboard or output files.

## Intentionally Not Included

This milestone does not include:

- Live Make API calls from this repository
- Make credentials
- Direct destination sync modules for Google Sheets, Airtable, or HubSpot
- Retry queues
- Background workers
- OAuth flows
- Dashboard UI
- Milestone 7 or later work
