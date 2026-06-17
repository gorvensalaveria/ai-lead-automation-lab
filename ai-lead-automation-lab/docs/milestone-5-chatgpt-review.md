# Milestone 5 ChatGPT Review Handoff

## Milestone

HubSpot Integration Foundation

## Scope Implemented

- Added HubSpot as an optional downstream dispatcher destination.
- Added HubSpot environment configuration.
- Added a dedicated HubSpot handler for contact property mapping and contact creation.
- Updated the integration dispatcher to include Google Sheets, Airtable, and HubSpot destination statuses.
- Preserved public webhook response compatibility.
- Preserved Google Sheets, Airtable, n8n, auth, HMAC, and idempotency behavior.
- Added HubSpot and dispatcher tests using mocks only.

## Files Changed

- `.env.example`
- `app/config.py`
- `app/integrations/hubspot.py`
- `app/integrations/dispatcher.py`
- `tests/test_hubspot_integration.py`
- `tests/test_integration_dispatcher.py`

No `/webhooks/leads` changes were made for this milestone.

## Important Behavior Implemented

HubSpot is disabled by default:

```dotenv
HUBSPOT_ENABLED=false
```

When HubSpot is disabled, the dispatcher returns an internal disabled destination status and does not call the HubSpot handler.

When HubSpot is enabled, the dispatcher calls `send_processed_lead_to_hubspot`. HubSpot delivery failures are non-blocking and return sanitized internal dispatcher status:

```json
{
  "destinations": {
    "hubspot": {
      "status": "failed",
      "error": "HubSpot delivery failed."
    }
  }
}
```

Successful HubSpot dispatch returns an internal success destination result:

```json
{
  "destinations": {
    "hubspot": {
      "status": "success",
      "result": {
        "status": "sent",
        "object_id": "contact_123"
      }
    }
  }
}
```

No public top-level `hubspot` webhook response key was added.

## HubSpot Configuration

Added:

```dotenv
HUBSPOT_ENABLED=false
HUBSPOT_ACCESS_TOKEN=
HUBSPOT_TIMEOUT_SECONDS=10
```

Missing HubSpot configuration does not affect local/browser behavior while HubSpot is disabled.

## HubSpot API Target

The handler targets:

```text
POST https://api.hubapi.com/crm/v3/objects/contacts
```

Headers:

```text
Authorization: Bearer <HUBSPOT_ACCESS_TOKEN>
Content-Type: application/json
```

Tests mock all HTTP calls. No real HubSpot API calls are made.

## HubSpot Field Mapping

The HubSpot payload maps processed lead data into contact properties:

- `email`
- `firstname`
- `lastname`
- `phone`
- `company`
- `lifecyclestage`
- `hs_lead_status`
- `ai_lead_score`
- `ai_classification`
- `ai_summary`
- `ai_follow_up`
- `lead_source`
- `lead_budget`
- `lead_timeline`

Name selection priority:

1. `crm_ready.contact_name`
2. `lead.contact.name`
3. `lead.name`

Name splitting:

- `Maria Santos` -> `firstname=Maria`, `lastname=Santos`
- `Maria` -> `firstname=Maria`, `lastname` omitted
- empty/missing -> both omitted

Scores and custom properties are sent as strings where possible. `None` values are omitted. Local output paths are not included in HubSpot properties.

## Error Handling

- Missing HubSpot token raises a safe `HubSpotConfigError`.
- HubSpot request failures raise a safe `HubSpotDeliveryError`.
- Raw HubSpot response bodies, tokens, Authorization headers, stack traces, and local file paths are not exposed in returned errors.
- HubSpot failures do not fail the main webhook response; they become internal dispatcher failures.

## Idempotency Compatibility

Existing idempotency behavior is preserved:

- Duplicate idempotency requests return the original saved successful response.
- Duplicate idempotency requests do not call `process_lead` again.
- Duplicate idempotency requests do not call the dispatcher again.
- Duplicate idempotency requests do not send again to Google Sheets.
- Duplicate idempotency requests do not send again to Airtable.
- Duplicate idempotency requests do not send again to HubSpot.
- Duplicate idempotency requests do not create duplicate outputs.

## Tests Added Or Updated

Added `tests/test_hubspot_integration.py` covering:

- HubSpot field mapping splits first and last name.
- Single-name contacts omit `lastname`.
- HubSpot payload shape is correct.
- Enabled but missing token raises safe config error.
- Enabled and configured sends one contact create request.
- Configured timeout is used.
- Expected endpoint is used.
- Authorization header uses Bearer token.
- HubSpot API failure raises safe delivery error.
- Delivery errors do not expose secrets.
- Optional missing fields are omitted safely.
- Local output paths are not included in HubSpot properties.

Updated `tests/test_integration_dispatcher.py` covering:

- Dispatcher includes HubSpot disabled status.
- Dispatcher calls HubSpot when enabled.
- Dispatcher does not call HubSpot when disabled.
- Dispatcher returns sanitized failed status for missing HubSpot config.
- Dispatcher includes Google Sheets, Airtable, and HubSpot destination statuses internally.
- Existing Google Sheets and Airtable dispatcher behavior remains passing.

## Test Commands

HubSpot:

```bash
python3 -m pytest tests/test_hubspot_integration.py
```

Result:

```text
8 passed
```

Dispatcher:

```bash
python3 -m pytest tests/test_integration_dispatcher.py
```

Result:

```text
13 passed
```

Auth and idempotency:

```bash
python3 -m pytest tests/test_webhook_auth.py tests/test_idempotency.py
```

Result:

```text
20 passed
```

Full suite:

```bash
python3 -m pytest
```

Result:

```text
121 passed, 74 warnings
```

Warnings are Starlette/FastAPI deprecation warnings under Python 3.14 and are non-blocking.

## Known Limitations

- HubSpot only creates one contact per processed lead.
- No HubSpot duplicate detection was added.
- No HubSpot update/upsert logic was added.
- No search-before-create was added.
- No company or deal creation was added.
- No pipeline or stage management was added.
- No OAuth, token refresh, or HubSpot app installation flow was added.
- HubSpot custom properties may not exist in a real portal; API errors are handled safely.
- HubSpot dispatcher results remain internal and are not exposed in the public webhook response.

## Out Of Scope Confirmation

No work was done for:

- OAuth flow
- Token refresh
- HubSpot app installation flow
- HubSpot duplicate detection
- HubSpot update/upsert
- Search-before-create
- Company/deal creation
- Pipeline/stage management
- Dashboard UI
- Retry queue
- Background worker
- n8n changes
- Make
- Zapier
- Frontend redesign
- Public webhook response changes
- Milestone 6 or later work

## Review Request

Please review whether Milestone 5 satisfies the approved HubSpot Integration Foundation architecture and whether it is ready to be accepted before moving to the next milestone.
