# AI Lead Intake Automation System

Beginner-friendly AI automation portfolio project for qualifying, summarizing, scoring, and preparing follow-up messages for new business leads.

## Recommended Portfolio Positioning

**Project name:** AI Lead Intake Automation System

**GitHub repo name:** `ai-lead-automation-lab`

**GitHub description:** AI automation system that processes leads, summarizes intent, scores quality, and drafts follow-up messages for business workflows.

## Business Problem

Many businesses receive leads from forms, messages, ads, or emails. Teams often spend too much time manually reading each lead, checking whether the lead is worth pursuing, writing notes, and preparing follow-up messages.

This project demonstrates how AI automation can support that workflow.

## Project Solution

This system will eventually:

1. Accept new lead information.
2. Store the lead data locally.
3. Summarize the lead.
4. Classify the lead as hot, warm, or cold.
5. Identify intent, pain point, and urgency.
6. Generate a lead score.
7. Draft a personalized follow-up message.
8. Save the automation output for review or CRM integration.

## Target Users

This project is designed for:

- Agencies
- Consultants and coaches
- SaaS businesses
- Real estate teams
- E-commerce businesses
- Appointment-based businesses
- Service companies hiring remote Filipino AI automation talent

## Skills Demonstrated

Over the full project, this portfolio will demonstrate:

- AI workflow automation
- OpenAI API usage
- Prompt engineering for business workflows
- Lead intake automation
- Lead qualification
- Lead scoring
- AI summarization
- AI classification
- Follow-up email and message generation
- CRM automation concepts
- Email automation concepts
- Google Sheets, Airtable, and Slack automation concepts
- Webhook basics
- API integration basics
- JSON data processing
- Environment variable management
- Error handling
- Logging
- Local data storage
- Client-friendly documentation
- Basic testing

## Milestone Plan

### Milestone 1: Project Setup

Create the project structure, `requirements.txt`, `.env.example`, `.gitignore`, and README draft only.

### Milestone 2: Sample Lead Data

Create sample lead input data in JSON.

### Milestone 3: Local Lead Loading

Load and validate lead data locally.

### Milestone 4: AI Lead Summary

Use the OpenAI API to summarize a lead.

### Milestone 5: AI Lead Classification

Use the OpenAI API to classify a lead as hot, warm, or cold.

### Milestone 6: Lead Scoring

Generate a lead score based on fit, urgency, budget, and intent.

### Milestone 7: Follow-Up Draft

Generate a personalized follow-up email or message draft.

### Milestone 8: Local Output Storage

Save automation output locally as JSON or SQLite.

### Milestone 9: Terminal Workflow

Add a simple terminal-based workflow that runs the full automation.

### Milestone 10: Error Handling and Logging

Add basic error handling and logging.

### Milestone 11: Basic Tests

Add pytest tests for lead loading, output format, and storage.

### Milestone 12: FastAPI Webhook

Add FastAPI webhook endpoints after the terminal version works.

### Milestone 13: Automation Platform Documentation

Add optional n8n, Make.com, and Zapier integration documentation.

### Milestone 14: Portfolio Polish

Polish the README for GitHub portfolio and client presentation.

## Current Status

Current milestone: **Milestone 8 complete**

Milestone 8 saves the full automation output locally as a JSON file. External integrations and tests have not been added yet.

## Project Structure

```text
ai-lead-automation-lab/
├── app/
│   ├── config.py
│   ├── main.py
│   └── automation/
│       ├── lead_loader.py
│       ├── summarizer.py
│       ├── classifier.py
│       ├── scorer.py
│       ├── message_generator.py
│       ├── storage.py
│       └── logger.py
├── data/
│   ├── leads/
│   └── outputs/
├── integrations/
│   ├── n8n/
│   ├── make/
│   └── zapier/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## What Each Folder and File Is For

`app/` contains the Python application code.

`app/config.py` manages environment variables such as the OpenAI API key and model name.

`app/main.py` will become the terminal entry point for running the automation.

`app/automation/` contains small modules for each automation step.

`app/automation/lead_loader.py` loads and validates lead data from local JSON files.

`app/automation/summarizer.py` summarizes lead details using the OpenAI API.

`app/automation/classifier.py` classifies leads as hot, warm, or cold using the OpenAI API.

`app/automation/scorer.py` calculates a lead quality score with a simple breakdown.

`app/automation/message_generator.py` drafts follow-up emails or messages using the OpenAI API.

`app/automation/storage.py` saves automation results locally as JSON files.

`app/automation/logger.py` will handle logging later.

`data/leads/` will store sample lead input files.

`data/outputs/` will store generated automation results.

`integrations/` is reserved for future n8n, Make.com, and Zapier documentation.

`tests/` will contain pytest tests in a later milestone.

`.env.example` shows which environment variables the project will need.

`.gitignore` prevents secrets, virtual environments, cache files, and generated outputs from being committed.

`requirements.txt` lists Python packages needed for the current milestone.

`README.md` explains the project, target users, milestone plan, and structure.

## AI Automation Concept for This Milestone

Milestone 8 is about **local output storage**.

After generating the AI summary, classification, score, and follow-up message, the next step is to save the result.

This project saves one JSON output file per processed lead. The saved output includes:

- Processing timestamp
- Original lead data
- AI summary
- AI classification
- Lead score
- Follow-up message draft

This makes the workflow easier to review and prepares the project for later CRM, Google Sheets, Airtable, Slack, n8n, Make, or Zapier integrations.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file:

```bash
cp .env.example .env
```

Then add your real OpenAI API key to `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-nano
APP_ENV=development
```

Run the local lead loader, AI summarizer, AI classifier, lead scorer, follow-up message generator, and output saver:

```bash
python3 -m app.main
```

Expected output:

```text
AI Lead Intake Automation System - Milestone 8
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

Hi Noah,
...

Saved Output:
data/outputs/lead_004_20260521T160000Z.json
```
