# Milestone 1 ChatGPT Review Handoff

## Milestone

Secure Webhook Foundation

## Scope Implemented

- API key validation for `POST /webhooks/leads`
- Optional HMAC signature verification
- HMAC timestamp tolerance checking
- Idempotency key support
- Config and `.env.example` additions
- SQLite storage support for idempotency keys
- Tests for webhook auth and idempotency

## Files Changed

- `.env.example`
- `app/config.py`
- `app/api.py`
- `app/automation/storage.py`
- `app/security/__init__.py`
- `app/security/webhook_auth.py`
- `tests/test_webhook_auth.py`
- `tests/test_idempotency.py`

## Implementation Summary

The `/webhooks/leads` route now reads the raw request body before parsing JSON so HMAC verification can use the exact payload bytes. Authentication runs before rate limiting. Idempotency lookup runs before rate limiting, so duplicate requests return the original saved successful response without processing the lead again or appending to Google Sheets again.

Webhook authentication is controlled through environment configuration. The code default for `WEBHOOK_AUTH_ENABLED` is `false` to preserve local browser intake and existing tests, while `.env.example` shows the production-recommended `WEBHOOK_AUTH_ENABLED=true`.

HMAC verification is implemented in `app/security/webhook_auth.py` as an independent helper. All signature and timestamp failures return:

```json
{
  "detail": "Invalid webhook signature."
}
```

If HMAC is enabled without a configured secret, the route returns HTTP 500:

```json
{
  "detail": "Webhook HMAC is enabled but not configured."
}
```

Invalid raw JSON now returns HTTP 400:

```json
{
  "detail": "Invalid JSON payload."
}
```

## Storage Changes

SQLite initialization now creates:

```sql
CREATE TABLE IF NOT EXISTS idempotency_keys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT UNIQUE NOT NULL,
  lead_id TEXT,
  file_name TEXT,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

Added storage helpers:

- `load_idempotency_response`
- `save_idempotency_response`

Only successful webhook responses are saved. Failed responses are not saved to the idempotency table.

## Tests Added

Added coverage for:

- Auth disabled preserves existing webhook behavior
- Missing API key returns 401 when auth is enabled
- Invalid API key returns 401 when auth is enabled
- Valid API key allows processing
- HMAC rejects missing signature
- HMAC rejects malformed signature
- HMAC rejects invalid signature
- HMAC rejects malformed timestamp
- HMAC rejects expired timestamp
- HMAC accepts a valid signature
- HMAC enabled without secret returns server config error
- Invalid JSON returns required 400 response
- First idempotency request processes normally
- Duplicate idempotency request returns saved response
- Duplicate idempotency request does not call `process_lead` again
- Duplicate idempotency request does not append to Google Sheets again
- Duplicate idempotency request does not create a second output
- Failed responses are not saved for idempotency
- Idempotency table is created

## Test Commands

Targeted tests:

```bash
python3 -m pytest tests/test_webhook_auth.py tests/test_idempotency.py
```

Result:

```text
19 passed
```

Full test suite:

```bash
python3 -m pytest
```

Result:

```text
84 passed, 70 warnings
```

The warnings are framework deprecation warnings from Starlette/FastAPI under Python 3.14.

## Known Limitations

- Replay protection is timestamp-tolerance based only. Nonce/signature storage was intentionally not added in Milestone 1.
- Duplicate idempotency responses do not include fresh rate-limit headers because idempotency is checked before rate limiting by design.
- HMAC timestamp tolerance rejects timestamps too far in either direction by using absolute age.

## Out Of Scope

No work was done for:

- Airtable
- HubSpot
- n8n
- Make
- Zapier
- Dashboard retry
- Client documentation
- Integration dispatcher
- Frontend redesign
- Advanced AI features

## Review Request

Please review whether Milestone 1 satisfies the approved Secure Webhook Foundation architecture and whether it is ready to be accepted before moving to the next milestone.
