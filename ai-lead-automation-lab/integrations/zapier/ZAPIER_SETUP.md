# Zapier Setup Guide

This guide shows how to create a Zapier workflow that sends leads into the FastAPI AI Lead Intake Automation backend.

Zapier sends the lead to FastAPI. FastAPI processes the lead with AI and handles downstream Google Sheets, Airtable, and HubSpot dispatch through the app's integration dispatcher.

Zapier should not directly sync to Google Sheets, Airtable, or HubSpot in this milestone.

## Recommended Zap

```text
Trigger: Webhooks by Zapier - Catch Hook
Action: Webhooks by Zapier - Custom Request or POST
Optional Action: Filter by Zapier for hot/qualified leads
Optional Action: Slack/Email notification placeholder
```

## Step 1: Create The Catch Hook

1. Create a new Zap.
2. Select **Webhooks by Zapier**.
3. Choose **Catch Hook**.
4. Copy the generated webhook URL.
5. Send `sample-webhook-payload.json` to the hook to test the trigger.

## Step 2: Add The FastAPI Request

Add **Webhooks by Zapier** as an action.

Choose **Custom Request** or **POST**.

Use:

```text
POST {{LEAD_API_BASE_URL}}/webhooks/leads
```

Set payload type to JSON.

## Step 3: Set Headers

Add:

```text
Content-Type: application/json
X-API-Key: {{LEAD_API_KEY}}
Idempotency-Key: {{generated_or_mapped_key}}
```

## Step 4: Map The Request Body

Map the incoming Zapier lead fields into the app-compatible payload:

```json
{
  "lead_id": "zapier_{{generated_or_mapped_key}}",
  "source": "{{source}}",
  "submitted_at": "{{zap_meta_timestamp}}",
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

## Step 5: Optional Filter For Qualified Leads

Add **Filter by Zapier** after the FastAPI request.

Example condition:

```text
classification equals hot
OR
lead score greater than or equal to 75
```

## Step 6: Optional Notification

Add a Slack, email, or internal notification placeholder for hot or qualified leads.

Do not include secrets or raw API responses in public notifications.

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

Add:

```text
X-Webhook-Timestamp: <unix_timestamp_seconds>
X-Webhook-Signature: sha256=<hex_digest>
```

Do not add placeholder HMAC headers unless the Zap computes the exact expected signature.

## What Is Not Included

This milestone does not include:

- Direct destination sync actions for Google Sheets, Airtable, or HubSpot
- OAuth flows
- Retry queues
- Background workers
- Dashboard UI
- Live Zapier credentials
- Make or n8n changes
