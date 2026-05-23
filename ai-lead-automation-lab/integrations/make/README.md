# Make.com Integration Notes

Milestone 13 does not add a live Make.com scenario. This document explains how Make.com could connect to the FastAPI webhook added in Milestone 12.

## Goal

Use Make.com to send lead data to:

```text
POST /webhooks/leads
```

## Example Make.com Scenario

1. Add a trigger module, such as **Webhooks**, **Google Forms**, **Facebook Lead Ads**, or **Airtable**.
2. Add an **HTTP** module.
3. Choose **Make a request**.
4. Set method to `POST`.
5. Set the request URL to the deployed FastAPI endpoint.
6. Set body type to JSON.
7. Map lead fields into the expected request body.
8. Use the response to create a CRM note, send an email draft, notify Slack, or update Airtable.

## Local Development URL

When running locally:

```bash
uvicorn app.api:app --reload
```

the endpoint is:

```text
http://127.0.0.1:8000/webhooks/leads
```

For Make.com cloud scenarios, the API must be deployed or exposed through a secure tunnel.

## Required JSON Fields

The API expects:

- `lead_id`
- `source`
- `submitted_at`
- `business_type`
- `contact.first_name`
- `contact.last_name`
- `contact.email`
- `contact.phone`
- `contact.company`
- `lead_details.service_interest`
- `lead_details.message`
- `lead_details.budget_range`
- `lead_details.timeline`
- `lead_details.preferred_contact_method`

## Example Use Cases

- Send hot leads to Slack.
- Add lead scores to Airtable.
- Create follow-up drafts for review.
- Route urgent leads to a sales pipeline.
- Store processed AI outputs for audit or reporting.

## Future Production Notes

Before using this with real leads:

- Deploy the FastAPI API securely.
- Add authentication.
- Use HTTPS.
- Add retry handling.
- Set OpenAI API usage limits.
