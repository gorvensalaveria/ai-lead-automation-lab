# AI Lead Automation Operating System

## Problem Statement

Many businesses receive leads from forms, ads, workflow tools, and landing pages, but review them manually. Teams spend time reading every message, judging lead quality, writing follow-up notes, and copying data into spreadsheets or CRMs.

## Solution Summary

I built a production-style AI lead automation system that processes inbound leads, generates AI summaries and follow-up drafts, classifies lead quality, calculates a score, saves results for review, dispatches to optional integrations, and tracks downstream delivery failures.

## Tech Stack

- Python
- FastAPI
- OpenAI API
- SQLite
- JSON storage
- Google Sheets API
- Airtable API
- HubSpot CRM API
- n8n workflow assets
- Make starter blueprint
- Zapier setup guide
- pytest
- Vanilla HTML, CSS, and JavaScript

## Key Features

- Browser lead intake page
- Secure webhook endpoint
- AI summary, classification, and follow-up generation
- Rule-based lead scoring
- Saved lead history dashboard
- Lead detail review page
- CSV export
- Google Sheets dispatch
- Airtable dispatch
- HubSpot contact creation
- Integration run tracking
- Manual retry for failed integration runs
- System status dashboard
- Documentation and demo handoff package

## Automation Workflow

```text
Lead source
  -> FastAPI webhook or browser intake
  -> AI processing
  -> JSON + SQLite storage
  -> integration dispatcher
  -> Google Sheets, Airtable, HubSpot
  -> integration status dashboard and retry
```

## Security and Reliability Features

- API key validation for webhook requests
- Optional HMAC signature verification
- Timestamp tolerance for replay protection
- Idempotency keys for safe client retries
- Rate limiting before expensive AI processing
- Request IDs and structured logs
- Non-blocking downstream integration failures
- Integration run records
- Manual retry of failed runs

## Integrations

- Google Sheets: spreadsheet handoff and optional auto-append.
- Airtable: optional record creation.
- HubSpot: optional contact creation.
- n8n: starter workflow for sending leads to FastAPI.
- Make: documented starter blueprint for sending leads to FastAPI.
- Zapier: setup guide for sending leads to FastAPI.

Make, Zapier, and n8n do not directly write to Google Sheets, Airtable, or HubSpot in this project. FastAPI owns AI processing and downstream dispatch.

## Testing Summary

The test suite covers webhook security, HMAC, idempotency, storage, dispatcher behavior, provider handlers with mocked HTTP calls, workflow assets, integration run tracking, manual retry, dashboard rendering, and documentation assets.

## What I Learned

- How to turn an AI workflow into an operational system.
- How to design secure webhook intake with idempotency.
- How to keep downstream failures non-blocking.
- How to separate integration dispatch from lead processing.
- How to document automation systems for both technical and non-technical reviewers.

## Future Improvements

- Production admin auth for dashboard endpoints
- Background retry queue
- OAuth-based CRM setup
- HubSpot and Airtable upsert support
- Deployment-specific runbooks
- Richer dashboard filtering and integration diagnostics

## Suggested Portfolio Blurb

Built a production-style AI lead automation system using FastAPI, OpenAI, secure webhooks, idempotency, Google Sheets, Airtable, HubSpot, n8n, Make, Zapier, integration run tracking, and manual retry tooling.
