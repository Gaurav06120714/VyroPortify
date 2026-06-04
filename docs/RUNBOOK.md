# VyroPortify Production Runbook

Operational playbook for incidents, on-call response, and routine maintenance.

---

## Severities

| Sev | Definition | Page on-call? | Status page? |
|---|---|---|---|
| **S1** | Site down, billing broken, data loss / leak | Immediately | Yes |
| **S2** | Core flow degraded (uploads failing, AI 5xx > 25%) | Within 15 min | Yes if > 30 min |
| **S3** | Non-critical degradation (analytics down, slow page) | Within 1 h | No |
| **S4** | Cosmetic / single-user | Next business day | No |

---

## On-Call

- **Primary** — rotates weekly (PagerDuty schedule `vyro-primary`).
- **Secondary** — escalation if primary unresponsive in 10 min.
- **Hand-off** — Mondays 09:00 local. Outgoing primary writes a 3-line
  summary in `#oncall-handoff`.

---

## Alert Catalog → Response

### `api.5xx_rate_high` (Sev 2)
- Open Grafana → API panel; identify the endpoint with the spike.
- Check Sentry for grouped exceptions in the last 15 min.
- If a recent deploy: roll back via Railway "redeploy previous" or
  `gh workflow run deploy-backend.yml -f ref=<previous-tag>`.

### `db.connection_saturation` (Sev 1)
- Inspect active connections: `SELECT count(*) FROM pg_stat_activity;`
- Kill stuck queries > 30 s: `SELECT pg_cancel_backend(pid) FROM …`
- If runaway worker: stop Celery (Railway worker service → Stop).

### `stripe.webhook_failures` (Sev 2)
- Confirm signature secret hasn't rotated in the Stripe dashboard.
- Check Redis idempotency keys (`webhook:stripe:*`) — duplicate retries
  are expected, missing keys means cache outage; clear the related
  event from the Stripe dashboard "Failed events" view and replay.

### `ai.provider_failover_sustained` (Sev 3)
- Indicates Anthropic is down and OpenRouter is taking all traffic.
- Watch token-cost dashboard — OpenRouter free models have lower quality;
  if user complaints rise, communicate via status page.

### `disk.r2_bucket_usage > 80%` (Sev 3)
- Rotate old resume objects: tombstone any soft-deleted resume > 30 d.
- If a single user is the cause, flag for billing review.

---

## Common Operations

### Promote a release to prod
```bash
gh workflow run deploy-backend.yml -f ref=v1.x.y
gh workflow run deploy-frontend.yml -f ref=v1.x.y
# Watch staging smoke + canary in #deploys; promote canary → 100% manually.
```

### Roll back the backend
```bash
gh workflow run deploy-backend.yml -f ref=<previous-tag>
# Verify with: curl https://api.vyroportify.com/api/v1/health/ready
```

### Restart Celery workers without downtime
```bash
# Railway dashboard → worker service → Redeploy.
# Tasks are acks_late=True so in-flight messages re-queue.
```

### Force-clear AI prompt cache (e.g. after a bad model push)
```bash
redis-cli --scan --pattern 'ai:prompt:*' | xargs redis-cli DEL
```

### Re-process a missed Stripe webhook
```bash
# In Stripe dashboard → Developers → Events → find the event → "Resend".
# Idempotency key in Redis prevents double processing for 24 h, so a
# replay outside that window is safe.
```

---

## Postmortem Template

```
# Incident: <title>
Date: YYYY-MM-DD · Severity: S1/S2 · Duration: <minutes>
Owner: <name> · Status: Draft / Approved

## Summary
2–3 sentences. What broke, who was affected, when it was fixed.

## Timeline (UTC)
- HH:MM — alert fires
- HH:MM — on-call ack
- HH:MM — root cause identified
- HH:MM — mitigation applied
- HH:MM — verified resolved

## Impact
- Users affected: …
- Requests failed: …
- Revenue impact: $…

## Root cause
…

## What went well
…

## What went wrong / could be better
…

## Action items
- [ ] (owner, due date) …
```
