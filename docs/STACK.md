# Tech Stack

A plain-English map of every piece of VyroPortify and what it does.

## Where the code lives

```
       Users / browsers
              │
              ▼
   ┌──────────────────────┐
   │  Vercel (frontend)   │  Next.js 15 + TypeScript + Tailwind
   └──────────┬───────────┘
              │ HTTPS
              ▼
   ┌──────────────────────┐
   │  Render Web Service  │  FastAPI (uvicorn)  ┐
   │   vyroportify-api    │  Celery worker      │  share one container
   └──┬───────────────┬───┘                     ┘  via backend/start.sh
      │               │
      ▼               ▼
 ┌──────────┐    ┌──────────┐
 │ Postgres │    │  Redis   │  (Render Key Value)
 │ portifyai│    │          │  queue + cache
 └──────────┘    └──────────┘

External APIs the backend calls:
  • Clerk      — authentication
  • Stripe     — payments
  • Gemini / OpenRouter / Anthropic — AI completions
  • S3 / R2    — portfolio HTML uploads
  • Resend     — transactional email
```

## Frontend — Vercel

| Tool | Why |
|---|---|
| **Next.js 15** | App-router framework |
| **TypeScript** | Type safety |
| **Tailwind CSS 4** | Styling |
| **Clerk React SDK** | Login / signup / OTP / OAuth UI |
| **TanStack Query** | Data fetching + cache |
| **Sonner** | Toast notifications |
| **Framer Motion** | Animations |
| **PostHog + Sentry** | Analytics + error tracking |

Hosted on **Vercel Hobby (free)**. Auto-deploys on every push to `main`.
Live at https://vyroportify.vercel.app.

## Backend — Render

| Tool | Why |
|---|---|
| **Python 3.14** | Language |
| **FastAPI** | Async HTTP framework |
| **Uvicorn** | ASGI server |
| **SQLAlchemy 2.0 (async)** | ORM |
| **asyncpg** | Postgres async driver |
| **Alembic** | DB migrations |
| **Celery** | Background jobs |
| **redis-py** | Redis client (cache + Celery broker) |
| **svix** | Clerk webhook signature verification |
| **boto3** | S3 / R2 uploads |
| **stripe** | Stripe SDK |
| **anthropic / google-generativeai / httpx** | AI providers |
| **slowapi** | Rate limiting |
| **OpenTelemetry** | Optional tracing |

Hosted on **Render free Web Service**. One container runs:
- `alembic upgrade head` (boot)
- `celery -A app.workers.celery_app worker` (background)
- `uvicorn app.main:app` (foreground)

Defined in [`backend/start.sh`](../backend/start.sh).

## Database — Render Postgres

Database name: **`portifyai`** (Render free tier, 90-day expiry).

Tables grouped by feature:

| Group | Tables |
|---|---|
| Core | `users`, `portfolios`, `resumes`, `ai_jobs`, `templates`, `template_reviews` |
| Multi-tenancy (v2.0) | `organizations`, `memberships`, `audit_events` |
| Analytics (v2.0+) | `portfolio_views`, `resume_exports` |
| Platform (v3.x) | `api_keys`, `webhook_endpoints`, `webhook_deliveries`, `oauth_apps`, `oauth_authorization_codes`, `oauth_access_tokens`, `sso_configs` |

19 alembic migrations: `0001_initial` → `0019_user_phone`.

## Cache + queue — Render Key Value (Redis-compatible)

Used for:

| Purpose | Key pattern | TTL |
|---|---|---|
| Celery task broker | `celery-task-meta-…` | per task |
| AI prompt cache | `ai:prompt:<sha256>` | 24 h |
| Per-IP rate limits | (slowapi internal) | window |
| Per-account daily quota | `quota:<bucket>:<user>:<day>` | until UTC midnight |
| Webhook receiver throttle | `wh:rate:<endpoint>:<minute>` | 120 s |
| Stripe webhook idempotency | `webhook:stripe:<event_id>` | configurable |

## External services

| Service | Purpose |
|---|---|
| **Clerk** | Login, signup, password, email-OTP, phone-OTP, Google, GitHub. Mirrors users to Postgres via a signed webhook to `/api/v1/auth/clerk-webhook`. |
| **Stripe** | Subscription billing. Sends webhooks to `/api/v1/billing/webhook` for plan upgrades / downgrades. |
| **Gemini → OpenRouter → Anthropic** | AI failover chain inside `app/services/ai_client.py`. |
| **S3 / R2** | Stores the generated portfolio HTML. Falls back to inline storage in `portfolios.content` JSONB if upload fails. |
| **Resend** | Transactional email (welcome, plan-changed, portfolio-published). |

## Costs today

| Service | Plan | Monthly |
|---|---|---|
| Vercel | Hobby | $0 |
| Render Web Service | Free (sleeps after 15 min idle) | $0 |
| Render Postgres | Free (90-day expiry) | $0 |
| Render Key Value | Free | $0 |
| Clerk | Free (≤10 000 MAU) | $0 |
| Stripe | Per-transaction (2.9 % + $0.30 US) | $0 fixed |
| Sentry | Developer | $0 |
| **Total fixed monthly** | | **$0** |

When to upgrade: see [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#known-limits-of-the-current-free-tier-setup).

## Where to look in the code

| Need | File |
|---|---|
| Add a new API route | `backend/app/routers/*.py` |
| Add a DB column | `backend/app/models/*.py` + `alembic revision --autogenerate` |
| Add a Celery task | `backend/app/workers/tasks/*.py` + register in `celery_app.py` |
| Add a frontend page | `frontend/src/app/...` |
| Add a frontend component | `frontend/src/components/...` |
| Tweak rate limits | `backend/app/core/limiter.py` + `slowapi` decorators on routes |
| Tweak daily quotas | `backend/app/services/quota.py` |
| Tweak Clerk public routes | `frontend/src/middleware.ts` |
