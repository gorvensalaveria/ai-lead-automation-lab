# Milestone 4 ChatGPT Review Handoff

## Milestone

n8n Workflow Readiness

## Scope Implemented

- Added n8n workflow readiness assets.
- Added an import-ready n8n starter workflow JSON.
- Added a simple external sample lead payload.
- Added secure header documentation.
- Expanded n8n setup documentation.
- Added asset validation tests.
- Added a short main README reference to the n8n docs.

## Files Changed

- `README.md`
- `integrations/n8n/README.md`
- `integrations/n8n/lead-intake-ai-automation.workflow.json`
- `integrations/n8n/sample-webhook-payload.json`
- `integrations/n8n/sample-secure-headers.md`
- `tests/test_n8n_assets.py`

No FastAPI app behavior was changed for this milestone.

## Important Behavior / Assets Added

The n8n workflow starter template demonstrates:

1. Lead intake through an n8n Webhook trigger.
2. Normalization from a simple external lead payload into the FastAPI app's expected `/webhooks/leads` schema.
3. Idempotency key generation.
4. HTTP request to:

```text
{{ $env.LEAD_API_BASE_URL }}/webhooks/leads
```

5. Required request headers:

```text
Content-Type: application/json
X-API-Key: {{ $env.LEAD_API_KEY }}
Idempotency-Key: <generated key>
```

6. Classification/score routing for hot or qualified leads.
7. Sales notification placeholder.
8. Explanation that Google Sheets and Airtable handoff happens inside FastAPI through the integration dispatcher.
9. Error branch placeholder.

The workflow is documented as an import-ready starter template. The README notes that node versions or credentials may need adjustment depending on the n8n version.

## Sample Payload

Added `sample-webhook-payload.json` in the simple external lead format requested by the architect:

- `name`
- `email`
- `phone`
- `company`
- `industry`
- `budget`
- `timeline`
- `source`
- `pain_point`
- `message`

The sample uses generic fictional data only.

## HMAC Documentation

HMAC is documented as optional advanced security only.

The workflow does not require HMAC by default and does not claim to compute HMAC signatures.

`sample-secure-headers.md` documents:

- `X-API-Key`
- `Idempotency-Key`
- `X-Webhook-Timestamp`
- `X-Webhook-Signature`
- HMAC payload format: `"{timestamp}.{raw_body}"`
- Signature format: `sha256=<hex_digest>`

## Compatibility Notes

This milestone did not modify:

- `/webhooks/leads`
- Webhook auth behavior
- HMAC behavior
- Idempotency behavior
- Integration dispatcher behavior
- Airtable behavior
- Google Sheets behavior

n8n sends leads to FastAPI. FastAPI remains responsible for AI processing and downstream Google Sheets/Airtable dispatch.

## Tests Added

Added `tests/test_n8n_assets.py` covering:

- n8n README exists.
- workflow JSON exists.
- sample payload exists.
- secure headers doc exists.
- workflow JSON is valid JSON.
- workflow has a webhook trigger node.
- workflow has an HTTP Request node.
- workflow references `/webhooks/leads`.
- workflow references `X-API-Key`.
- workflow references `Idempotency-Key`.
- sample payload is valid JSON.
- sample payload contains required fields.
- docs explain FastAPI owns downstream dispatch.
- docs explain optional HMAC header format.
- assets do not contain obvious real secrets.

## Test Commands

n8n asset tests:

```bash
python3 -m pytest tests/test_n8n_assets.py
```

Result:

```text
8 passed
```

Full suite:

```bash
python3 -m pytest
```

Result:

```text
109 passed, 74 warnings
```

Warnings are Starlette/FastAPI deprecation warnings under Python 3.14 and are non-blocking.

## Known Limitations

- The n8n workflow is a starter template and may require node version or credential adjustments after import.
- HMAC signing is documented but not implemented in the workflow.
- The workflow does not directly write to Google Sheets or Airtable.
- The workflow does not include live n8n credentials.
- No running n8n instance is required or tested.
- No retry queue, background worker, or dashboard UI was added.

## Out Of Scope Confirmation

No work was done for:

- Make
- Zapier
- HubSpot
- Retry queue
- Dashboard UI
- Frontend redesign
- Background workers
- Live n8n credential dependencies
- Milestone 5 or later work

## Review Request

Please review whether Milestone 4 satisfies the approved n8n Workflow Readiness architecture and whether it is ready to be accepted before moving to the next milestone.
