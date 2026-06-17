# Demo Script

## Opening Pitch

"This is an AI Lead Automation Operating System. It takes an inbound lead, uses AI to summarize and classify it, calculates a lead score, drafts a follow-up message, saves everything for human review, and sends the result to optional tools like Google Sheets, Airtable, and HubSpot. It also tracks integration failures and lets an operator retry them from a status dashboard."

## Step 1: Submit a Sample Lead

Open:

```text
/lead-intake
```

Use the sample lead button or enter a fictional lead. Submit the lead and wait for processing.

Talking point:

"This simulates a lead coming from a website form, ad funnel, automation tool, or webhook."

## Step 2: Show AI Summary, Classification, and Follow-Up

Point out:

- AI summary,
- hot/warm/cold classification,
- score,
- follow-up draft,
- saved output link.

Talking point:

"The output is not just a chatbot response. It is structured, saved, and ready for review or CRM handoff."

## Step 3: Show Lead History

Open:

```text
/history
```

Show:

- saved leads,
- filters,
- status workflow,
- CSV export,
- detail page.

Talking point:

"A human reviewer can manage the lead queue instead of losing AI outputs in logs or one-off messages."

## Step 4: Show Integrations

Explain:

- Google Sheets can receive processed lead rows.
- Airtable can receive lead records.
- HubSpot can receive contacts.

Talking point:

"All integrations are optional. FastAPI handles downstream delivery through one dispatcher, so the workflow can grow without rewriting the webhook."

## Step 5: Show n8n, Make, and Zapier Assets

Open the `integrations/` folder.

Show:

- n8n workflow starter,
- Make starter blueprint,
- Zapier setup guide,
- sample payloads,
- secure header docs.

Talking point:

"These tools are upstream entry points. They send the lead into FastAPI. FastAPI performs the AI processing and dispatches to Google Sheets, Airtable, or HubSpot."

## Step 6: Show Integration Status Dashboard

Open:

```text
/system-status
```

Show:

- enabled providers,
- last status,
- success count,
- failed count,
- recent failed runs.

Talking point:

"This is the operations view. It gives a reviewer visibility into whether downstream handoffs are working."

## Step 7: Show Failed Retry Behavior

If a failed run exists, click Retry. If not, explain the behavior:

- retry calls the existing backend retry API,
- the original provider is retried,
- retry count increments,
- successful retries disappear from the failed list after refresh.

Talking point:

"This is manual, human-in-the-loop reliability. There is no hidden background worker in this version."

## Closing Pitch for Employers or Clients

"This project demonstrates practical AI automation beyond a prototype: secure webhooks, idempotency, structured storage, CRM-ready handoff, multiple integration paths, failure tracking, manual retry, tests, and client-ready documentation. It is designed to be understandable for business users and reviewable by technical teams."

## 60-Second Version

"This is an AI lead automation system built with FastAPI and OpenAI. A lead enters through a browser form, webhook, n8n, Make, or Zapier. The app summarizes the lead, classifies it, scores it, drafts follow-up, saves the result, and optionally sends it to Google Sheets, Airtable, or HubSpot. It has API key security, optional HMAC, idempotency, SQLite history, integration run tracking, a status dashboard, and manual retry for failed deliveries. The project is fully tested and documented for client or employer handoff."
