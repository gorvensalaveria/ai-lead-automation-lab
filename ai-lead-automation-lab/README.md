# AI Lead Intake Automation System

AI automation portfolio project that processes inbound leads, summarizes business needs, classifies lead quality, calculates a lead score, drafts a follow-up message, and saves the result for review or future CRM integration.

## Portfolio Summary

**Project name:** AI Lead Intake Automation System

**Repository name:** `ai-lead-automation-lab`

**Short description:** AI automation system that processes leads, summarizes intent, scores quality, and drafts follow-up messages for business workflows.

**Target role:** AI Automation Specialist / AI Automation Developer

**Target clients and employers:** agencies, consultants, coaches, SaaS businesses, real estate teams, e-commerce businesses, appointment-based businesses, and service companies hiring remote Filipino AI automation talent.

## Business Problem

Many businesses receive leads from forms, messages, ads, emails, or booking pages. Teams often spend too much time manually reading each lead, deciding whether it is worth pursuing, writing notes, and drafting follow-up messages.

This project shows how AI automation can reduce that manual work while still keeping the final output reviewable by a human.

## What This Project Does

The workflow can:

1. Load lead data from JSON or receive it through a FastAPI webhook.
2. Validate required lead fields.
3. Use the OpenAI API to summarize the lead.
4. Use the OpenAI API to classify the lead as `hot`, `warm`, or `cold`.
5. Generate a rule-based lead score using fit, urgency, budget, and intent.
6. Use the OpenAI API to draft a personalized follow-up message.
7. Save the full automation output locally as JSON.
8. Expose the workflow through a terminal command, webhook API, and simple browser demo.

## Current Status

Current milestone: **Product demo upgrade in progress**

The core portfolio version is complete. It includes the local terminal workflow, FastAPI webhook endpoint, browser demo page, logging, local JSON output storage, pytest tests, and documentation for future n8n, Make.com, and Zapier connections.

Live external integrations are documented but not implemented.

## Tech Stack

- Python
- OpenAI API
- FastAPI
- Uvicorn
- pytest
- python-dotenv
- JSON local storage
- Local logging

## Skills Demonstrated

- AI workflow automation
- OpenAI API usage
- Prompt engineering for business workflows
- Lead intake automation
- Lead qualification
- Lead scoring
- AI summarization
- AI classification
- Follow-up email/message generation
- Webhook/API basics
- JSON data processing
- Environment variables and API key management
- Error handling
- Logging
- Local output storage
- FastAPI endpoint design
- Simple web demo design
- Basic automated testing
- Client-friendly documentation
- n8n, Make.com, and Zapier integration planning

## Project Structure

```text
ai-lead-automation-lab/
├── app/
│   ├── api.py
│   ├── config.py
│   ├── demo_page.py
│   ├── main.py
│   ├── static/
│   │   ├── demo.css
│   │   └── demo.js
│   ├── templates/
│   │   └── demo.html
│   └── automation/
│       ├── classifier.py
│       ├── lead_loader.py
│       ├── logger.py
│       ├── message_generator.py
│       ├── scorer.py
│       ├── storage.py
│       ├── summarizer.py
│       └── workflow.py
├── data/
│   ├── leads/
│   └── outputs/
├── integrations/
│   ├── make/
│   ├── n8n/
│   └── zapier/
├── logs/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Key Files

`app/main.py` is the terminal entry point.

`app/api.py` exposes FastAPI endpoints:

- `GET /`
- `GET /demo`
- `GET /health`
- `POST /webhooks/leads`

`app/demo_page.py` loads the browser demo HTML template.

`app/templates/demo.html` contains the browser demo page markup.

`app/static/demo.css` contains the browser demo styling.

`app/static/demo.js` contains the browser demo sample lead and result rendering behavior.

`app/automation/workflow.py` contains the shared workflow used by both the terminal command and FastAPI API.

`app/automation/lead_loader.py` loads and validates lead JSON.

`app/automation/summarizer.py` summarizes lead details using the OpenAI API.

`app/automation/classifier.py` classifies leads as `hot`, `warm`, or `cold`.

`app/automation/scorer.py` calculates a lead quality score.

`app/automation/message_generator.py` drafts follow-up messages using the OpenAI API.

`app/automation/storage.py` saves processed outputs as JSON.

`app/automation/logger.py` writes local workflow logs.

`data/leads/` contains sample lead JSON files.

`data/outputs/` stores generated local output files.

`integrations/` documents future n8n, Make.com, and Zapier workflows.

`tests/` contains pytest tests.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-nano
APP_ENV=development
```

Do not commit `.env` to GitHub.

## Run The Terminal Workflow

Run the default sample lead:

```bash
python3 -m app.main
```

Run a specific lead file:

```bash
python3 -m app.main --lead-file data/leads/lead_004_saas.json
```

Run with a custom output folder:

```bash
python3 -m app.main --lead-file data/leads/lead_004_saas.json --output-dir data/outputs
```

Example output:

```text
AI Lead Intake Automation System
Lead file: data/leads/lead_004_saas.json
Loaded lead: lead_004
Business type: saas
Contact: Noah Mitchell
Company: PipelineMetric
Interest: sales workflow automation
Status: Lead data loaded and validated successfully.

AI Summary:
The lead is a SaaS company interested in sales workflow automation...

AI Classification:
hot

Lead Score:
100/100 (high)
Breakdown: fit=25, urgency=25, budget=25, intent=25

Follow-Up Message Draft:
Subject: Helping PipelineMetric qualify demo requests faster

Saved Output:
data/outputs/lead_004_20260522T134038Z.json
```

## Run The FastAPI Webhook API

Start the API server:

```bash
uvicorn app.api:app --reload
```

Open the browser demo:

```text
http://127.0.0.1:8000/demo
```

The demo page lets a user enter lead details, click **Process Lead**, and view:

- AI summary
- Hot/warm/cold classification
- Lead score and rating
- Score breakdown
- Follow-up message draft
- Saved output path

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Process a lead through the webhook endpoint:

```bash
curl -X POST http://127.0.0.1:8000/webhooks/leads \
  -H "Content-Type: application/json" \
  -d @data/leads/lead_004_saas.json
```

## Output Format

Each successful run saves a JSON file in `data/outputs/`.

The saved output includes:

- Processing timestamp
- Original lead data
- AI-generated summary
- AI lead classification
- Lead score and score breakdown
- AI-generated follow-up message draft
- CRM-ready flattened output for future spreadsheet, CRM, or automation platform handoff

Generated `.json` output files are ignored by Git because real outputs may contain lead or customer information.

## Demo Leads

The project includes sample demo leads for common client conversations:

- `data/leads/demo_hot_saas.json`
- `data/leads/demo_warm_coaching.json`
- `data/leads/demo_cold_general.json`

The browser demo also has quick-fill buttons for hot, warm, and cold examples.

## Tests

Run tests:

```bash
python3 -m pytest
```

The current tests cover:

- API health endpoint
- Browser demo page
- Invalid webhook lead validation
- Lead JSON loading
- Missing lead file handling
- Required field validation
- Output result structure
- CRM-ready output structure
- Local JSON output saving

The tests do not call the OpenAI API, so they run without spending API credits.

## Logs

Logs are written locally to:

```text
logs/app.log
```

Generated `.log` files are ignored by Git.

## Integration Notes

The project includes documentation for future automation platform connections:

- [n8n integration notes](integrations/n8n/README.md)
- [Make.com integration notes](integrations/make/README.md)
- [Zapier integration notes](integrations/zapier/README.md)

These docs explain how each platform could send lead JSON to:

```text
POST /webhooks/leads
```

## Milestone History

1. Project setup
2. Sample lead JSON data
3. Local lead loading and validation
4. OpenAI lead summarization
5. OpenAI hot/warm/cold classification
6. Rule-based lead scoring
7. OpenAI follow-up message draft
8. Local JSON output storage
9. Terminal workflow
10. Error handling and logging
11. pytest tests
12. FastAPI webhook endpoints
13. n8n, Make.com, and Zapier documentation
14. README polish for GitHub portfolio presentation
15. Simple FastAPI browser demo and CRM-ready output block

## Portfolio Talking Point

This project demonstrates a practical AI automation workflow for businesses that receive inbound leads and need faster qualification, prioritization, follow-up drafting, and CRM-ready handoff.

It is intentionally beginner-friendly, but it uses real-world building blocks: structured JSON, OpenAI API calls, validation, scoring logic, FastAPI webhooks, local storage, logging, and tests.
