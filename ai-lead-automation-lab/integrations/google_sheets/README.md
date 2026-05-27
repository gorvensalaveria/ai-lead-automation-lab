# Google Sheets Integration Notes

This integration package documents the Google Sheets handoff shape for the AI Lead Intake Automation System.

The current product includes a tested payload adapter and preview API endpoints. It does not write directly to a live Google Sheet yet, which keeps the portfolio review experience open while showing the exact data contract needed for a production integration.

## Use Case

Many small teams want qualified leads in a spreadsheet before they are ready for a full CRM. This adapter turns saved AI lead results into flat rows that can be appended to Google Sheets by:

- a future backend Google Sheets API client
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

## Production Upgrade Path

To make this a live Google Sheets integration:

1. Create a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a service account and share the target Sheet with that service account email.
4. Store credentials as a deployment secret.
5. Add a protected backend endpoint or background job that calls `spreadsheets.values.append`.
6. Record an audit event such as `google_sheets_exported` after a successful append.

For a client-facing production version, the write action should be protected by authentication or an API gateway because lead records can contain personal contact information.
