# Zapier Integration Notes

This document explains how Zapier can connect to the AI Lead Intake Automation System through the FastAPI webhook endpoint.

## Goal

Use Zapier to send lead data to:

```text
POST /webhooks/leads
```

## Example Zap

1. Choose a trigger app, such as **Facebook Lead Ads**, **Typeform**, **Google Forms**, **HubSpot**, or **Webhooks by Zapier**.
2. Add an action step using **Webhooks by Zapier**.
3. Choose **POST**.
4. Set the URL to the deployed FastAPI endpoint.
5. Set payload type to JSON.
6. Map the lead fields into the expected request body.
7. Use the response in later Zap steps, such as Gmail, Slack, Google Sheets, Airtable, or a CRM.

If `GOOGLE_SHEETS_AUTO_APPEND=true`, the backend can also append the processed lead to Google Sheets automatically after saving it locally.

## Local Development URL

When running locally:

```bash
uvicorn app.api:app --reload
```

the endpoint is:

```text
http://127.0.0.1:8000/webhooks/leads
```

Zapier cloud cannot normally reach `127.0.0.1` on your computer. For Zapier testing, the API must be deployed or exposed through a secure tunnel.

## Example Zapier Field Mapping

- Lead ID -> `lead_id`
- Source -> `source`
- Submitted time -> `submitted_at`
- Business type -> `business_type`
- First name -> `contact.first_name`
- Last name -> `contact.last_name`
- Email -> `contact.email`
- Phone -> `contact.phone`
- Company -> `contact.company`
- Service interest -> `lead_details.service_interest`
- Message -> `lead_details.message`
- Budget range -> `lead_details.budget_range`
- Timeline -> `lead_details.timeline`
- Preferred contact method -> `lead_details.preferred_contact_method`

## Future Production Notes

Before using this with real leads:

- Deploy the API.
- Add authentication.
- Use HTTPS.
- Avoid exposing private lead data in public logs.
- Review OpenAI API usage and budget limits.
