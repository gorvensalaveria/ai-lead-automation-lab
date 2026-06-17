# Zapier Secure Headers

Use these headers in **Webhooks by Zapier** when sending leads to FastAPI:

```text
POST {{LEAD_API_BASE_URL}}/webhooks/leads
```

## Required When Webhook Auth Is Enabled

```text
X-API-Key: {{LEAD_API_KEY}}
```

## Recommended For Reliability

```text
Idempotency-Key: {{generated_or_mapped_key}}
```

Reuse the same idempotency key when retrying the same lead submission.

## Optional Advanced Security

HMAC is optional and disabled by default locally. API key plus idempotency is the recommended starter setup for Zapier.

If `WEBHOOK_HMAC_ENABLED=true`, include:

```text
X-Webhook-Timestamp: <unix_timestamp_seconds>
X-Webhook-Signature: sha256=<hex_digest>
```

The signed payload format is:

```text
"{timestamp}.{raw_body}"
```

The signature format is:

```text
sha256=<hex_digest>
```

Do not add placeholder HMAC headers unless your Zap computes the exact expected signature from the exact raw JSON body it sends to FastAPI.

## Starter Headers

```text
Content-Type: application/json
X-API-Key: {{LEAD_API_KEY}}
Idempotency-Key: {{generated_or_mapped_key}}
```
