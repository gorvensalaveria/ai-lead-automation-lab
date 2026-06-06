# n8n Integration Notes

This document explains how n8n can connect to the AI Lead Intake Automation System through the FastAPI webhook endpoint.

## Goal

Use n8n to send lead data to the local API endpoint:

```text
POST /webhooks/leads
```

## Example n8n Workflow

1. Add a **Webhook** trigger node.
2. Receive lead data from a form, CRM, ad platform, or test request.
3. Add an **HTTP Request** node.
4. Set method to `POST`.
5. Set URL to the deployed API endpoint.
6. Send the lead payload as JSON.
7. Use the API response to update a CRM, send a Slack alert, or trigger another handoff step. If `GOOGLE_SHEETS_AUTO_APPEND=true`, the backend can also append the processed lead to Google Sheets automatically.

## Local Development URL

When running locally with:

```bash
uvicorn app.api:app --reload
```

the local webhook processing endpoint is:

```text
http://127.0.0.1:8000/webhooks/leads
```

For real n8n cloud usage, the API must be deployed or exposed through a secure tunnel.

## Expected Request Body

```json
{
  "lead_id": "lead_004",
  "source": "consultation_request_form",
  "submitted_at": "2026-05-21T15:30:00+08:00",
  "business_type": "saas",
  "contact": {
    "first_name": "Noah",
    "last_name": "Mitchell",
    "email": "noah.mitchell@example.com",
    "phone": "+1 646 555 0142",
    "company": "PipelineMetric"
  },
  "lead_details": {
    "service_interest": "sales workflow automation",
    "message": "We need a better way to qualify inbound sales inquiries before our sales team spends time on calls. We use HubSpot and Slack.",
    "budget_range": "USD 2,000 - USD 5,000",
    "timeline": "urgent",
    "preferred_contact_method": "phone"
  }
}
```

## Expected Response

The API returns:

- Processing status
- Saved output path
- AI summary
- AI classification
- Lead score
- Follow-up message draft

## Future Production Notes

Before using this with real leads:

- Deploy the FastAPI app to a secure server.
- Add webhook authentication.
- Use HTTPS.
- Avoid sending sensitive data to public test endpoints.
- Confirm OpenAI API billing and usage limits.
