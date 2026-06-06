# Google Sheets Integration Notes

This integration package documents and supports the Google Sheets handoff for the AI Lead Intake Automation System.

The current product includes:

- a tested payload adapter
- preview API endpoints
- a live Google Sheets append endpoint
- optional auto-append after webhook lead processing

The live integration is disabled by default so the portfolio demo can run without Google credentials.

## Use Case

Many small teams want qualified leads in a spreadsheet before they are ready for a full CRM. This adapter turns saved AI lead results into flat rows that can be appended to Google Sheets by:

- a future backend Google Sheets API client
- the built-in backend Google Sheets API client
- n8n
- Make.com
- Zapier
- a custom operations script

## Preview Endpoints

Preview all saved leads as spreadsheet-ready rows:

```text
GET /api/integrations/google-sheets/preview
```

Preview one saved lead as a Google Sheets append payload:

```text
GET /api/integrations/google-sheets/preview/{saved_output_file_name}.json
```

Append one saved lead result to a configured live Google Sheet:

```text
POST /api/integrations/google-sheets/append/{saved_output_file_name}.json
```

The single-lead endpoint returns a payload shaped for the Google Sheets `spreadsheets.values.append` API:

```json
{
  "integration": "google_sheets",
  "payload": {
    "range": "Leads!A:T",
    "majorDimension": "ROWS",
    "columns": [
      "processed_at",
      "lead_id",
      "contact_name",
      "company",
      "email",
      "phone",
      "business_type",
      "service_interest",
      "classification",
      "lead_score",
      "max_score",
      "lead_rating",
      "review_status",
      "recommended_next_action",
      "summary",
      "follow_up_message",
      "source",
      "preferred_contact_method",
      "workflow_version",
      "model"
    ],
    "values": [
      ["2026-05-24T13:12:46Z", "web_123", "Taylor Morgan"]
    ]
  }
}
```

The example `values` row above is shortened for readability. The real payload includes one value for every column.

## Column Mapping

| Sheet column | Source |
| --- | --- |
| `processed_at` | saved result / CRM-ready fields |
| `lead_id` | CRM-ready fields / original lead |
| `contact_name` | CRM-ready fields |
| `company` | CRM-ready fields / original contact |
| `email` | CRM-ready fields / original contact |
| `phone` | CRM-ready fields / original contact |
| `business_type` | CRM-ready fields / original lead |
| `service_interest` | CRM-ready fields |
| `classification` | CRM-ready fields / AI output |
| `lead_score` | CRM-ready fields |
| `max_score` | CRM-ready fields |
| `lead_rating` | CRM-ready fields |
| `review_status` | SQLite review workflow |
| `recommended_next_action` | CRM-ready fields |
| `summary` | CRM-ready fields / AI output |
| `follow_up_message` | CRM-ready fields / AI output |
| `source` | CRM-ready fields / original lead |
| `preferred_contact_method` | CRM-ready fields |
| `workflow_version` | AI metadata |
| `model` | AI metadata |

## Live Integration Setup

To enable the live Google Sheets integration:

1. Create a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a service account and share the target Sheet with that service account email.
4. Store credentials locally or as a deployment secret.
5. Configure these environment variables:

```text
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=your_google_sheet_id_here
GOOGLE_SHEETS_RANGE=Leads!A:T
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
```

For hosted deployments, you can use `GOOGLE_SERVICE_ACCOUNT_JSON` instead of `GOOGLE_SERVICE_ACCOUNT_FILE`.

To automatically append every newly processed webhook lead to Google Sheets, also set:

```text
GOOGLE_SHEETS_AUTO_APPEND=true
```

After a successful append, the app records a `google_sheets_exported` audit event for the saved lead.

For a client-facing production version, the write action should be protected by authentication or an API gateway because lead records can contain personal contact information.
