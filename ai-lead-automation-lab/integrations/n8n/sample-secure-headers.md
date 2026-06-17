# Secure Headers For FastAPI Lead Webhook

The n8n workflow sends leads to:

```text
POST /webhooks/leads
```

## Required When Webhook Auth Is Enabled

```text
X-API-Key: {{ $env.LEAD_API_KEY }}
```

FastAPI validates this header when `WEBHOOK_AUTH_ENABLED=true`.

## Recommended For Reliability

```text
Idempotency-Key: <unique-lead-request-key>
```

Use the same idempotency key when retrying the same lead submission. FastAPI returns the original successful response and avoids duplicate processing for repeated keys.

## Optional When HMAC Is Enabled

HMAC is optional and disabled by default locally.

If `WEBHOOK_HMAC_ENABLED=true`, include:

```text
X-Webhook-Timestamp: <unix_timestamp_seconds>
X-Webhook-Signature: sha256=<hex_digest>
```

The signed payload format is:

```text
"{timestamp}.{raw_body}"
```

The signature is:

```text
HMAC_SHA256(WEBHOOK_HMAC_SECRET, "{timestamp}.{raw_body}")
```

The final header format is:

```text
X-Webhook-Signature: sha256=<hex_digest>
```

Do not add placeholder HMAC headers unless your n8n workflow computes the exact expected signature from the exact raw JSON body it sends to FastAPI.

## Example Basic Headers

```text
Content-Type: application/json
X-API-Key: {{ $env.LEAD_API_KEY }}
Idempotency-Key: {{$json.idempotency_key}}
```

These examples use placeholders only. Do not store real secrets in workflow JSON or documentation.
