# VyroPortify Backup & Disaster Recovery

**Objectives**: RPO ≤ 1 hour · RTO ≤ 4 hours.

---

## What we back up

| Asset | Mechanism | Retention | Owner |
|---|---|---|---|
| Postgres (Railway) | Daily automated snapshots | 30 days | Railway |
| Postgres point-in-time | WAL archiving (continuous) | 7 days | Railway |
| R2 / S3 resume objects | Bucket versioning enabled | 90 days | Cloudflare / AWS |
| Redis | Not backed up (cache only — rebuildable) | — | — |
| Stripe data | Source of truth at Stripe; we only mirror | — | Stripe |
| Application code | GitHub | Forever | GitHub |
| Secrets | 1Password vault `vyro-prod`, env vars in Railway/Vercel | — | Founders |

---

## Restore procedures

### Postgres — full restore

```bash
# 1. Pick the snapshot from Railway dashboard → Database → Backups.
# 2. Create a new database from the snapshot (Railway "Restore to new DB").
# 3. Update DATABASE_URL in the API + worker services to the restored DB.
# 4. Redeploy backend.
# 5. Verify:
curl https://api.vyroportify.com/api/v1/health/ready
psql "$DATABASE_URL" -c "SELECT count(*) FROM users;"
```

### Postgres — point-in-time

For data corruption recovery within the last 7 days:

```bash
# Railway dashboard → Database → "Restore to point in time"
# Specify the timestamp just BEFORE the bad event.
```

### R2 / S3 — restore a specific object

```bash
# List versions:
aws s3api list-object-versions --bucket vyroportify-resumes --prefix <user-id>/

# Restore a specific version:
aws s3api copy-object \
  --bucket vyroportify-resumes \
  --copy-source "vyroportify-resumes/<key>?versionId=<id>" \
  --key <key>
```

### Full-region failover

Currently single-region (Railway us-east). DR procedure for a Railway outage:

1. Spin up Fly.io app from `backend/Dockerfile`.
2. Attach the most recent Railway snapshot to a Neon Postgres instance.
3. Update Vercel `NEXT_PUBLIC_API_URL` to the Fly app URL.
4. Communicate via status page; RTO ≈ 4 h.

This is **manual today**. Automation planned for v2.0 (multi-region).

---

## Drill schedule

| Drill | Cadence | Last run |
|---|---|---|
| Postgres restore to staging | Quarterly | TBD |
| R2 object recovery | Quarterly | TBD |
| Full DR (Fly + Neon) | Annually | TBD |

A drill is only "passing" if:
1. The runbook above is followed verbatim (no extra knowledge required).
2. RTO is met.
3. Post-drill notes capture every step that needed clarification.

---

## Secrets rotation

| Secret | Rotation cadence | Procedure |
|---|---|---|
| `SECRET_KEY` | Yearly or on suspected leak | Generate via `openssl rand -hex 32`; update Railway env; redeploy |
| Stripe webhook secret | On compromise | Rotate in Stripe → update `STRIPE_WEBHOOK_SECRET` → redeploy |
| Clerk JWKS | Auto (Clerk-managed) | — |
| Resend API key | Yearly | Issue new key in Resend → update `RESEND_API_KEY` → redeploy → revoke old |
| AWS / R2 keys | Quarterly | Rotate in IAM/R2 → update env → redeploy → revoke old |

Always: **issue new → deploy → revoke old**, never the reverse.
