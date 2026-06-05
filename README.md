<div align="center">

# ⚡ VyroPortify

### Turn your resume into a stunning, hosted portfolio in under 60 seconds.

[![Next.js](https://img.shields.io/badge/Next.js_15-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Claude AI](https://img.shields.io/badge/Claude_AI-D97706?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com/)
[![Clerk](https://img.shields.io/badge/Clerk_Auth-6C47FF?style=for-the-badge&logo=clerk&logoColor=white)](https://clerk.dev/)
[![Stripe](https://img.shields.io/badge/Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/Gaurav06120714/vyroportify/actions/workflows/test.yml/badge.svg)](https://github.com/Gaurav06120714/vyroportify/actions)

</div>

---

## ✨ What It Does

VyroPortify uses Claude AI to transform your resume (or a quick form) into a beautiful, public portfolio website — hosted instantly, no code required.

| Feature | Free | Pro ($9/mo) |
|---|:---:|:---:|
| AI Resume Builder (12-step guided) | ✅ | ✅ |
| Portfolio templates | 1 | All 4 |
| Portfolios | 3 | Unlimited |
| AI skill suggestions | ❌ | ✅ |
| AI cover letter generator | ❌ | ✅ |
| Custom domain | ❌ | ✅ |
| Public URL (`/portfolio/your-name`) | ✅ | ✅ |

---

## 🎨 Templates

| Template | Style | Best For |
|---|---|---|
| **Aurora** | Dark electric, animated gradient | Developers & Designers |
| **Minimal** | Clean white, typography-first | PMs & Researchers |
| **Cyber** | Neon glassmorphism, terminal feel | Anyone who refuses to blend in |
| **Executive** | Two-column serif, gold accents | Senior Engineers & Managers |

---

## 🚀 Recently Shipped (v3.x)

| Tag | Theme |
|---|---|
| [`v3.0.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.0) | Public REST API + scoped personal API keys (`vp_…`) |
| [`v3.0.1`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.1) | Outbound webhooks — HMAC-signed, Celery-delivered, retried |
| [`v3.0.2`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.2) | OAuth 2.0 (authorization-code + PKCE) for third-party apps |
| [`v3.0.3`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.3) | White-label / custom theme for enterprise orgs |
| [`v3.0.4`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.4) | SOC 2 / GDPR: right-to-access, right-to-erasure, policy disclosure |
| [`v3.0.5`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.5) | SSO / SAML foundation (per-org IdP, email-domain discovery) |
| [`v3.1.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.1.0) | Admin analytics API (overview, time-series, top portfolios) |
| [`v3.2.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.2.0) | Bulk portfolio export as a streaming ZIP with manifest |
| [`v3.3.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.3.0) | Webhook event catalog + delivery replay |
| [`v3.3.1`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.3.1) | DDoS hardening: per-account quotas, scanner-path drop, receiver throttle |

See **[Security, Performance & DDoS Protection](#-security-performance--ddos-protection)** below for the full defence stack.

---

## 🗂 Project Structure

```
vyroportify/
├── frontend/                    # Next.js 15 · TypeScript · Tailwind CSS
│   ├── src/
│   │   ├── app/
│   │   │   ├── (marketing)/     # Landing page, pricing
│   │   │   ├── (dashboard)/     # All /dashboard/* pages
│   │   │   │   └── dashboard/
│   │   │   │       ├── page.tsx              # Overview
│   │   │   │       ├── build-resume/         # AI Resume Builder
│   │   │   │       ├── upload/               # PDF/DOCX upload
│   │   │   │       ├── portfolios/           # My Portfolios
│   │   │   │       ├── templates/            # Template picker
│   │   │   │       ├── cover-letter/         # AI Cover Letter
│   │   │   │       └── settings/             # Account + Billing
│   │   │   └── (auth)/          # Login, Register (Clerk)
│   │   ├── components/
│   │   │   ├── dashboard/       # Sidebar, MobileHeader
│   │   │   └── ui/              # Shared UI primitives
│   │   ├── context/             # ThemeContext, PlanContext
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # api.ts, posthog.ts, sentry.ts
│   │   └── types/               # Shared TypeScript types
│   ├── e2e/                     # Playwright end-to-end tests
│   └── src/test/                # Vitest unit tests
│
├── backend/                     # FastAPI · SQLAlchemy · Celery
│   ├── app/
│   │   ├── routers/             # auth, resume, portfolio, billing
│   │   ├── services/            # resume_parser, resume_builder, portfolio_generator
│   │   ├── models/              # User, Resume, Portfolio, AIJob (SQLAlchemy)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── core/                # config, rate limiter, cache, sentry
│   │   ├── templates/           # Jinja2 HTML (aurora, minimal, cyber, executive)
│   │   └── workers/             # Celery tasks
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile               # API server image
│   └── Dockerfile.worker        # Celery worker image
│
├── .github/workflows/           # CI/CD pipeline (GitHub Actions)
├── docker-compose.yml           # Local full-stack dev environment
└── README.md
```

---

## 🚀 Local Development

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| Python | 3.12+ | [python.org](https://python.org) |
| PostgreSQL | 16 | macOS: `brew install postgresql@16` / Windows: [postgresql.org](https://www.postgresql.org/download/windows/) |
| Redis | 7 | macOS: `brew install redis` / Windows: [redis.io](https://redis.io/docs/getting-started/installation/install-redis-on-windows/) |
| Vyro Browser | latest | [VyroBrowser](https://github.com/Gaurav06120714/VyroBrowser) *(optional)* |

### 1. Clone

**macOS**
```bash
git clone https://github.com/Gaurav06120714/vyroportify.git
cd vyroportify
```

**Windows**
```powershell
git clone https://github.com/Gaurav06120714/vyroportify.git
cd vyroportify
```

### 2. Frontend

**macOS**
```bash
cd frontend
npm install
cp .env.example .env.local   # fill in values below
npm run dev                  # → http://localhost:3007
```

**Windows**
```powershell
cd frontend
npm install
copy .env.example .env.local   # fill in values below
npm run dev                    # → http://localhost:3007
```

**`frontend/.env.local`**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/login
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/register
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_SITE_URL=http://localhost:3007

# Optional
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...
```

### 3. Backend

**macOS**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # fill in values below

createdb vyroportify
alembic upgrade head

uvicorn app.main:app --reload --port 8001   # → http://localhost:8001
```

**Windows**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env        # fill in values below

createdb vyroportify
alembic upgrade head

uvicorn app.main:app --reload --port 8001   # → http://localhost:8001
```

**`backend/.env`**
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vyroportify
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-32-chars-minimum
FRONTEND_URL=http://localhost:3007

# Optional
SENTRY_DSN=https://...@sentry.io/...
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=us-east-1
```

### 4. Run Everything + Open in Vyro Browser

**macOS**
```bash
# From project root — starts frontend + backend + opens in Vyro Browser
npm run dev:vyro

# Or start separately:
npm run dev          # starts both frontend + backend
```

**Windows**
```powershell
# From project root — starts frontend + backend + opens in Vyro Browser
npm run dev:vyro

# Or start separately:
npm run dev
```

> 💡 Opens automatically in **Vyro Browser** if installed. Falls back to default browser if not found.

### 5. Docker (alternative — runs everything at once)

```bash
docker compose up --build
```

---

## 🔑 API Reference

Base URL: `http://localhost:8001/api/v1`  
Interactive docs: [`/api/v1/docs`](http://localhost:8001/api/v1/docs)

```
# ── Resume / AI ──────────────────────────────────────────────────────────────
POST   /resume/build              AI resume builder            (6/hr · ai_build quota)
POST   /resume/suggest-skills     AI skill suggestions         (10/hr · ai_enhance quota)
POST   /resume/cover-letter       AI cover letter              (10/hr · ai_enhance quota)
POST   /resume/upload             Upload PDF / DOCX
GET    /resume/                   List user resumes

# ── Portfolio ────────────────────────────────────────────────────────────────
POST   /portfolio/generate        Generate portfolio           (10/min)
GET    /portfolio/{id}/status     Poll generation status
GET    /portfolio/p/{slug}        Public portfolio (edge-cached 5 min)
PUT    /portfolio/{id}/publish    Toggle public / private
DELETE /portfolio/{id}            Delete portfolio
GET    /portfolio/sitemap         All public slugs

# ── Public API (v3.0.0) — vp_… key OR oat_… OAuth token ─────────────────────
GET    /public/me                 Caller identity + granted scopes
GET    /public/portfolios         Paginated list (portfolios:read)
GET    /public/portfolios/{id}    Single portfolio (portfolios:read)
GET    /public/resumes            Paginated list (resumes:read)

# ── API Key management (v3.0.0) ─────────────────────────────────────────────
POST   /keys                      Issue API key (returns raw key once)
GET    /keys                      List caller's keys
DELETE /keys/{key_id}             Revoke

# ── Outbound Webhooks (v3.0.1 + v3.3.0) ─────────────────────────────────────
GET    /webhooks/events           Event catalog + signature scheme
POST   /webhooks                  Register endpoint (returns secret once)
GET    /webhooks                  List endpoints
DELETE /webhooks/{id}             Delete
GET    /webhooks/{id}/deliveries  Recent delivery audit
POST   /webhooks/{id}/test        Dispatch a `ping` event
POST   /webhooks/{id}/deliveries/{delivery_id}/replay   Re-fire a recorded payload

# ── OAuth 2.0 third-party apps (v3.0.2) ─────────────────────────────────────
POST   /oauth/apps                Register app (returns client_secret once)
GET    /oauth/apps                List own apps
DELETE /oauth/apps/{id}
GET    /oauth/authorize           Inspect an authorize request (consent screen prep)
POST   /oauth/consent             Issue one-time authorization code
POST   /oauth/token               Exchange code → access token (20/min)
GET    /oauth/grants              List apps holding tokens for the caller
DELETE /oauth/grants/{id}         Revoke

# ── Organizations & White-label (v2.0 + v3.0.3) ─────────────────────────────
GET    /organizations             List caller's orgs
POST   /organizations             Create org
GET    /organizations/{id}/branding         Read org branding (members)
PUT    /organizations/{id}/branding         Update branding (admin+, enterprise only)

# ── Admin Analytics (v3.1.0) ────────────────────────────────────────────────
GET    /analytics/orgs/{id}/overview        Headline counts
GET    /analytics/orgs/{id}/timeseries      Daily portfolios + views
GET    /analytics/orgs/{id}/top             Top portfolios by views

# ── Compliance / SOC 2 (v3.0.4) ─────────────────────────────────────────────
GET    /compliance/policies                 Public retention + subprocessor disclosure
GET    /compliance/me/export                Right-to-access export (Art. 15)
DELETE /compliance/me                       Right-to-erasure (Art. 17)
GET    /compliance/me/audit                 Caller's audit events

# ── SSO / SAML (v3.0.5) ─────────────────────────────────────────────────────
GET    /sso/login?domain=…                  Public IdP discovery
GET    /sso/configs/{org_id}                Read SAML config (admin+)
PUT    /sso/configs/{org_id}                Configure IdP (admin+, enterprise)
POST   /sso/acs                             SAML POST-binding ACS (stub)

# ── Bulk Export (v3.2.0) ────────────────────────────────────────────────────
GET    /bulk/portfolios.zip                 Streaming ZIP with manifest

# ── Billing / Auth / Health ─────────────────────────────────────────────────
POST   /billing/create-checkout             Stripe checkout
GET    /billing/status                      Subscription status
GET    /billing/portal                      Customer portal URL
GET    /auth/me                             Current user profile
GET    /health/ready                        Liveness + dependency probe
```

---

## 🌐 Deployment

### Frontend → Vercel

1. Import the `frontend/` directory at [vercel.com/new](https://vercel.com/new)
2. Add all `NEXT_PUBLIC_*` environment variables in the Vercel dashboard
3. Every push to `main` auto-deploys

### Backend → Railway

1. Create a Railway project, attach a **Postgres** and **Redis** service
2. Set all backend environment variables in Railway
3. Railway auto-reads `backend/railway.toml` and builds from `backend/Dockerfile`

### Required GitHub Secrets (Settings → Secrets → Actions)

| Secret | Description |
|---|---|
| `RAILWAY_TOKEN` | Railway API token |
| `VERCEL_TOKEN` | Vercel API token |
| `VERCEL_ORG_ID` | Vercel org ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (used in CI build) |
| `NEXT_PUBLIC_API_URL` | Production API URL |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog key *(optional)* |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN *(optional)* |

---

## 🧪 Testing

```bash
# Backend — pytest
cd backend
pytest -x -q

# Frontend — Vitest unit tests
cd frontend
npm test

# Frontend — type check + lint
npx tsc --noEmit
npx next lint

# Frontend — Playwright e2e
npx playwright test
```

---

## 🔐 Authentication — Password, Email OTP & Phone OTP

VyroPortify supports **three sign-in methods**, all powered by Clerk:

| Method | How it works |
|---|---|
| **Email + Password** | Classic credential login |
| **Email OTP** | One-time 6-digit code sent to the user's email |
| **Phone OTP (SMS)** | One-time 6-digit code sent via SMS |
| **Social (Google, GitHub)** | OAuth single-click sign-in |

The `<SignIn />` and `<SignUp />` components on `/login` and `/register` automatically render whichever factors are enabled in the Clerk dashboard — **no code change is required**.

### Enable OTP (one-time setup)

1. Open the **Clerk Dashboard** → your project → **User & Authentication → Email, Phone, Username**.
2. Toggle on:
   - ✅ **Email address** → *Verification: Email verification code*
   - ✅ **Phone number** → *Verification: SMS verification code*
3. Under **User & Authentication → Authentication strategies**, enable:
   - ✅ **Email verification code**
   - ✅ **SMS verification code**
   - (keep) **Password**, **Google**, **GitHub**
4. Save. The login/register pages immediately offer OTP options.

> 💡 Phone OTP requires a Clerk plan with SMS credits. Free tier ships ~100 SMS/mo.

### Backend impact

- Backend treats every authenticated request the same way — it verifies the Clerk JWT via JWKS (`app/security.py`). OTP vs password vs social is transparent to the API.
- New users created via OTP are auto-provisioned on first authenticated call (existing behavior).

---

## 🛡 Security, Performance & DDoS Protection

VyroPortify treats abuse-resistance as a first-class feature, not an afterthought.
Defences are layered so a single failure — a CDN outage, a leaked credential,
a misbehaving receiver — cannot take the platform down.

### Authentication & authorization

| Concern | Implementation |
|---|---|
| User auth | Clerk-issued JWTs (RS256), verified against the cached JWKS |
| Service-to-service auth | Personal API keys (`vp_…`), SHA-256 hashed at rest, scoped permissions |
| Third-party apps | OAuth 2.0 authorization-code flow with PKCE (S256), `oat_…` access tokens |
| RBAC | Per-org `owner / admin / editor / viewer`, enforced by `require_role` dependency |
| SSO (enterprise) | Per-org SAML config with email-domain discovery (`/api/v1/sso/login`) |

### Layered abuse defences

| Layer | Mechanism | Where it lives |
|---|---|---|
| **L3/L4 floods** | Cloudflare proxy + WAF + Bot Fight Mode (operator-configured) | `docs/DDOS_HARDENING.md` |
| **L7 scanner probes** | Middleware drops `/.env`, `/.git/`, `/wp-admin`, etc. → instant 404 | `app/main.py · ddos_hardening` |
| **Headless bots** | Empty / `<3`-char `User-Agent` rejected on `POST/PUT/PATCH/DELETE` | `app/main.py · ddos_hardening` |
| **Per-IP rate limit** | SlowAPI + Redis; proxy-aware key fn extracts `CF-Connecting-IP` | `app/core/limiter.py` |
| **Per-account daily quota** | Plan-aware Redis counters, expire at UTC midnight | `app/services/quota.py` |
| **Receiver amplification** | Outbound webhooks capped at 60 deliveries / endpoint / minute | `app/workers/tasks/deliver_webhook.py` |
| **OAuth brute-force** | `/oauth/token` rate-limited to 20/min | `app/routers/oauth.py` |
| **Oversized payloads** | Pre-handler size check against `MAX_REQUEST_BODY_BYTES` | `app/main.py · enforce_request_size_limit` |
| **Static-asset spikes** | Public portfolio pages set `Cache-Control: public, max-age=300, s-maxage=900` | `app/main.py · ddos_hardening` |
| **Prompt injection** | All user-supplied strings normalised through `sanitize_for_ai` before the model | `app/services/resume_parser.py` |
| **Signature replay** | Webhook header `X-VyroPortify-Signature: t=<unix>,v1=<hmac>` over `{t}.{body}`; ±5 min window | `app/services/webhooks.py` |

### Daily quotas (per-account, plan-aware)

| Bucket | Free | Pro | Enterprise |
|---|:---:|:---:|:---:|
| `ai_build` (resume / portfolio generation) | 5 / day | 50 / day | 500 / day |
| `ai_enhance` (cover letter, skill suggestions) | 10 / day | 200 / day | 2 000 / day |
| `bulk_export` (ZIP downloads) | 2 / day | 20 / day | 200 / day |

Quotas survive IP rotation — a distributed botnet cannot grind through the AI
budget by spreading requests across thousands of addresses on a single account.

### Web hardening

- **Security headers** — HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy on every response
- **CORS** — explicit allowlist; never `*`; production startup refuses to boot on misconfiguration
- **Idempotent webhooks** — Stripe events de-duplicated in Redis for `WEBHOOK_IDEMPOTENCY_TTL_SECONDS`
- **Audit log** — privileged actions persist to `audit_events`; structured security events flow to a separate `vyroportify.security` logger (SIEM-routable)

### Compliance surface (SOC 2 / GDPR readiness)

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/compliance/policies` | Public disclosure of retention, residency, subprocessors |
| `GET /api/v1/compliance/me/export` | Article 15 right-to-access export |
| `DELETE /api/v1/compliance/me` | Article 17 right-to-erasure with cascaded cleanup |
| `GET /api/v1/compliance/me/audit` | Caller-scoped audit-event history |

### Performance & observability

- **Prompt cache** — Redis-backed AI completions; cache hit rate logged per call
- **Provider failover** — Gemini → OpenRouter → Anthropic chain on transient errors
- **Public-page caching** — portfolios 1 h, sitemap 24 h
- **Image optimisation** — uploads compressed to WebP via Pillow before S3
- **OpenTelemetry** — opt-in tracing; no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset
- **Sentry** — frontend + backend error tracking, PII scrubbed at SDK level
- **PostHog** — analytics with Clerk auto-identification
- **Anti-flash theming** — inline script in `layout.tsx` applies the persisted theme before React hydrates

### Operational playbook

A full DDoS playbook lives in [`docs/DDOS_HARDENING.md`](docs/DDOS_HARDENING.md):
Cloudflare onboarding, Cloudflare Turnstile (CAPTCHA) wiring, nginx limits,
autoscale caps, Sentry alert thresholds, and a step-by-step incident-response
runbook.

---

## 🎨 Theme System

VyroPortify ships with a full **Light / Dark / System** theme:

- CSS custom properties (`--pf-*`) defined for both modes in `globals.css`
- `ThemeContext` applies the `dark` class to `<html>` and persists to `localStorage`
- Anti-flash inline script in `layout.tsx` resolves theme before first paint
- Smooth 200ms transitions across all color properties

---

## 🗺 Versioned Release Roadmap

A milestone-driven plan. Every sub-version ends with a **Review Gate → Commit → Tag → Push**. No work begins on the next sub-version until the gate passes.

### Version Map

| Version | Theme | Window |
|---|---|---|
| **v1.0** | MVP baseline (frozen, tagged) | now |
| **v1.1** | Foundation & Stability — authz, plan-gating, webhook hardening | 2–3 wk |
| **v1.2** | Core Feature Completion — email, custom domains, AI hardening, OG images, pagination | 3–4 wk |
| **v1.3** | UI/UX Modernization Pt.1 — design tokens, shadcn/ui, toasts, skeletons | 3 wk |
| **v1.4** | UI/UX Modernization Pt.2 — cmd-K, shortcuts, onboarding, settings, DataTable | 3 wk |
| **v1.5** | Performance & Security — OpenTelemetry, perf budgets, scans, CSP enforce | 2–3 wk |
| **v1.6** | Production Readiness — backups, DR, runbooks, readiness probes, deploy workflows | 2 wk |
| **v1.7** | Visual Refresh + Unified Builder — Gridlock-inspired clean palette, merge build-resume form + preview into a single split-pane page | 2–3 wk |
| **v2.0** | Enterprise GA — team workspaces, RBAC, audit-log UI, analytics, billing v2 | 6–8 wk |
| **v2.1** | Template marketplace (community + paid via Stripe Connect) | 4 wk |
| **v2.2** | i18n + PWA + mobile polish | 3 wk |
| **v2.3** | PDF Resume Export — ATS-friendly LaTeX resume.pdf | 3–4 wk |
| **v3.0** | Platform — public API, webhooks, OAuth apps, white-label, SOC 2, SSO/SAML | **shipped** |
| **v3.1** | Admin analytics API for organizations | **shipped** |
| **v3.2** | Bulk portfolio export (streaming ZIP + manifest) | **shipped** |
| **v3.3** | Webhook event catalog + delivery replay + DDoS hardening | **shipped** |

### v1.1 — Foundation & Stability

| Sub | Scope | Effort | Risk |
|---|---|---|---|
| v1.1.0 | Authorization audit + `assert_owner()` helper + cross-tenant tests | 4 d | High |
| v1.1.1 | Backend `require_plan("pro")` dependency on all Pro endpoints | 2 d | Med |
| v1.1.2 | Stripe webhook idempotency (Redis 24h TTL) + replay protection | 2 d | High |
| v1.1.3 | `error.tsx`, `global-error.tsx`, route-level boundaries | 1 d | Low |
| v1.1.4 | Repo hygiene: PG version pin, duplicate file cleanup, doc sync | 1 d | Low |

### v1.2 — Core Feature Completion

| Sub | Scope | Effort | Risk |
|---|---|---|---|
| v1.2.0 | Transactional email (Resend): welcome, publish, plan-change | 3 d | Low |
| v1.2.1 | Custom domain (Pro) — CNAME verify + DB field + attach API | 5 d | High |
| v1.2.2 | AI hardening — prompt caching, provider failover, cost telemetry | 3 d | Med |
| v1.2.3 | OG image generation via `@vercel/og` | 1 d | Low |
| v1.2.4 | Cursor pagination on list endpoints | 2 d | Low |

### v1.3 — UI/UX Modernization Pt.1

| Sub | Scope | Effort |
|---|---|---|
| v1.3.0 | Design tokens in `tailwind.config.ts` | 2 d |
| v1.3.1 | shadcn/ui primitives (Button, Input, Dialog, etc.) | 4 d |
| v1.3.2 | Toast (`sonner`) wired in `Providers.tsx` | 1 d |
| v1.3.3 | Skeleton variants + empty states with illustrations | 2 d |
| v1.3.4 | Typography scale + motion (respects `prefers-reduced-motion`) | 1 d |

### v1.4 — UI/UX Modernization Pt.2

| Sub | Scope | Effort |
|---|---|---|
| v1.4.0 | `cmdk` command palette | 2 d |
| v1.4.1 | Keyboard shortcuts + `?` cheatsheet | 1 d |
| v1.4.2 | Onboarding checklist + sample portfolio seed | 3 d |
| v1.4.3 | Settings sub-nav architecture | 2 d |
| v1.4.4 | Portfolios DataTable (TanStack) — sort/filter/bulk | 3 d |

### v1.5 — Performance & Security

| Sub | Scope | Effort |
|---|---|---|
| v1.5.0 | OpenTelemetry (FastAPI + Celery + Next.js) → Grafana | 3 d |
| v1.5.1 | Lighthouse-CI budgets (LCP ≤ 2.5s, CLS ≤ 0.1) | 2 d |
| v1.5.2 | Rate limiting on `/auth/*`, `/billing/*`, public reads | 1 d |
| v1.5.3 | Dependabot + Trivy + pip-audit + gitleaks + SBOM | 1 d |
| v1.5.4 | CSP report-only → enforce | 1 d + 1 wk observation |

### v1.6 — Production Readiness

| Sub | Scope | Effort |
|---|---|---|
| v1.6.0 | PG snapshots (30d retention), R2 versioning, restore drill | 3 d |
| v1.6.1 | Runbooks, on-call rotation, postmortem template | 2 d |
| v1.6.2 | `/readiness` probe + autoscaling policy | 1 d |
| v1.6.3 | Schemathesis contract tests (nightly) | 2 d |
| v1.6.4 | `deploy-frontend.yml` + `deploy-backend.yml` with canary | 2 d |

### v1.7 — Visual Refresh + Unified Builder

**Inspiration**: [Gridlock 2.0 (HackerEarth × Flipkart)](https://gridlock2point0.hackerearth.com/) —
clean, civic-modern aesthetic: white/off-white surfaces, deep-blue primary, warm
amber accents for CTAs, modern sans-serif (system stack or Inter), generous
whitespace, **no glows / no neon / no glassmorphism**. The current Aurora dark
palette stays available as an alternate theme; the new "Clarity" palette
becomes the default.

| Sub | Scope | Effort | Risk |
|---|---|---|---|
| v1.7.0 | "Clarity" light palette — add token set + theme switch | 2 d | Low |
| v1.7.1 | Typography pass — Inter / Geist Sans, refined scale | 1 d | Low |
| v1.7.2 | Marketing + dashboard restyle to the new palette | 3 d | Med |
| v1.7.3 | Unify `/dashboard/build-resume` + `/dashboard/portfolios/[id]/preview` into one split-pane page (`/dashboard/builder/[id]`) | 4 d | Med |
| v1.7.4 | Live preview wiring — form changes patch a debounced preview iframe | 2 d | Med |
| v1.7.5 | Mobile responsive — collapses to tabs (Edit / Preview) under `lg` | 1 d | Low |

#### v1.7.0 — Clarity palette tokens

Add a second theme alongside Aurora. Switchable via `data-theme` on `<html>`
(set by `ThemeContext`).

```css
[data-theme="clarity"] {
  --pf-bg:           #ffffff;
  --pf-surface:      #fafbfc;
  --pf-surface2:     #f4f6f8;
  --pf-text:         #0f172a;       /* slate-900 */
  --pf-text-dim:     #334155;       /* slate-700 */
  --pf-muted:        #64748b;       /* slate-500 */
  --pf-accent:       #2563eb;       /* Gridlock blue */
  --pf-accent-hover: #1d4ed8;
  --pf-accent-soft:  rgba(37,99,235,0.10);
  --pf-cta-warm:     #f59e0b;       /* amber CTA */
  --pf-border-light: rgba(15,23,42,0.08);
  --pf-border:       rgba(15,23,42,0.14);
  --pf-elev-1: 0 1px 2px rgba(15,23,42,0.04);
  --pf-elev-2: 0 4px 12px rgba(15,23,42,0.06);
}
```

- Honors the v1.5 contrast ratios (`--pf-text` on `--pf-bg` = 16:1).
- The Aurora dark palette stays under `[data-theme="aurora"]`; theme toggle
  flips between the two with anti-flash inline script.

#### v1.7.1 — Typography

- Headings & body: **Inter** (already loaded for the marketing site, extend
  to dashboard) with Geist Sans fallback.
- Type scale unchanged (uses v1.3 tokens).
- Drop letter-spacing on display headings (-0.02em) to match Gridlock's
  cleaner look.
- Replace `font-extrabold` (800) on hero with `font-bold` (700) — less
  shouty, matches the civic-modern feel.

#### v1.7.2 — Restyle

Page-by-page swap:
- `(marketing)/page.tsx` — hero, features, pricing, FAQ
- `(dashboard)/dashboard/page.tsx` — overview
- `Sidebar.tsx` — accent → blue, hover → slate-50
- Buttons → primary uses `--pf-accent`; warm CTA variant uses `--pf-cta-warm`
- Cards → drop heavy shadow, add 1px slate-100 border instead
- Remove all `shadow-[0_0_16px_var(--pf-border-hover)]` glow effects

#### v1.7.3 — Unified Builder (the merge)

Replace two pages with one:

```
/dashboard/build-resume          ─┐
                                  ├─→  /dashboard/builder/[id]
/dashboard/portfolios/[id]/preview ─┘
```

**Layout** (desktop, lg+):
```
┌─────────────────────────────────────────────────────────┐
│  Header: Save status · Template picker · Publish ⌄      │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  Form (left, 480px)  │  Live Preview (right, fluid)     │
│  Sticky StepShell     │  iframe → /portfolio/preview     │
│  with 12 sections     │                                  │
│  collapsible accordion│                                  │
│                      │                                  │
└──────────────────────┴──────────────────────────────────┘
```

- Routes affected: `(dashboard)/dashboard/builder/[id]/page.tsx` (new),
  old `build-resume` becomes a redirect for ~1 minor (deprecation),
  old `portfolios/[id]/preview` becomes a 302 to `builder/[id]?tab=preview`.
- State: `useReducer` on the resume payload; URL search params for
  `?step=`, `?tab=preview` so deep links survive refresh.
- Save semantics: debounced (800ms) `PATCH /api/v1/resume/{id}` on each
  field commit, with a header status pill (`Saved · 2s ago`).

#### v1.7.4 — Live preview wiring

- Form changes → debounced PATCH → preview iframe receives a `postMessage`
  → preview re-renders from cached payload (no extra fetch).
- Fall back to a 2s polling interval if `postMessage` channel breaks
  (cross-origin in prod).
- Skeleton swap during initial render — uses existing `PortfolioCardSkeleton`.

#### v1.7.5 — Mobile

- `<lg`: form and preview become tabbed (`Edit` / `Preview`). Tab state in
  URL search param so refresh preserves it.
- Sticky bottom CTA (`Publish` / `Next step`) — matches the rest of the
  dashboard mobile pattern.
- Preview tab uses pinch-zoom on the iframe for full-page viewing.

**Dependencies / prerequisites**

- v1.3 token system (used as the substrate for the new palette).
- v1.4 SettingsNav pattern (informs the layout idiom).
- No backend changes required for v1.7.0–v1.7.2.
- v1.7.3 needs `PATCH /api/v1/resume/{id}` to accept partial bodies —
  endpoint exists, confirm Pydantic schema is `exclude_unset` friendly.

**Expected outcomes**

- Aurora and Clarity both ship; default flips to Clarity for new users,
  existing users keep their current theme.
- One canonical builder page instead of two — fewer route changes per
  edit, shorter onboarding journey.
- All Lighthouse a11y/perf budgets from v1.5.1 still pass.

**Risks**

- Existing pages re-styled in v1.7.2 may briefly break visual tests
  (no Chromatic in repo) — mitigate by previewing on Vercel preview
  deploys before promoting.
- Combining two routes is a deep-link breaking change for anyone with
  bookmarks. Mitigation: keep both legacy routes as 302 redirects for
  at least one minor.

---

### v2.0 — Enterprise GA

| Sub | Scope | Effort | Risk |
|---|---|---|---|
| v2.0.0 | Team workspaces (`Organization`, `Membership`) | 8 d | High |
| v2.0.1 | RBAC (owner/admin/editor/viewer) | 4 d | Med |
| v2.0.2 | Audit log UI (search/export) | 3 d | Low |
| v2.0.3 | Per-portfolio analytics (views/visitors/geo/CTR) | 4 d | Med |
| v2.0.4 | Billing v2 — per-seat + usage add-ons | 4 d | High |
| v2.0.5 | Backfill: personal accounts → single-member orgs | 3 d | High |

### v2.1 — Template Marketplace
v2.1.0 community submission + moderation · v2.1.1 paid templates via Stripe Connect · v2.1.2 ratings/reviews/search

### v2.2 — i18n + PWA + Mobile
v2.2.0 `next-intl` (en/es/fr/de/hi/ja) · v2.2.1 PWA manifest + service worker · v2.2.2 mobile gestures + bottom-tab nav

### v2.3 — PDF Resume Export (LaTeX → ATS-friendly resume.pdf)

**Objective**: when a user has filled in their profile (personal details,
education, skills, projects, experience, certifications, achievements), they
can click *Download PDF* and receive a clean, modern, ATS-parseable
`resume.pdf` rendered from a LaTeX template — no manual formatting,
consistent output across all users.

| Sub | Scope | Effort | Risk |
|---|---|---|---|
| v2.3.0 | LaTeX template + Jinja2 binding (Tectonic engine in Docker) | 5 d | Med |
| v2.3.1 | Backend service + Celery task for async render | 3 d | Med |
| v2.3.2 | `POST /api/v1/resume/{id}/export-pdf` → returns presigned URL | 2 d | Low |
| v2.3.3 | Frontend *Download PDF* CTA + loading + Sonner toast | 2 d | Low |
| v2.3.4 | Three template variants (Modern, Classic, Compact) + per-user pick | 4 d | Low |
| v2.3.5 | ATS validation pass (Affinda / OpenResume parser smoke test) | 2 d | Med |

**Implementation outline**

- **Engine**: [Tectonic](https://tectonic-typesetting.github.io/) (self-contained
  LaTeX, no full TeX Live install). Runs inside the Celery worker image; first
  build downloads fonts/packages into a cached volume.
- **Template**: single `resume.tex.j2` rendered via Jinja2 (escape-mode `latex`)
  with strict context: `personal`, `summary`, `experience[]`, `education[]`,
  `skills[]`, `projects[]`, `certifications[]`, `achievements[]`. All optional
  blocks suppress empty sections cleanly — no "Experience:" with nothing below.
- **ATS hygiene rules baked into the template**:
  - Single-column layout (multi-column kills parsers).
  - Standard section names (`Experience`, `Education`, `Skills`, `Projects`).
  - No images, no icons in headings, no text inside graphics.
  - `\hypersetup{hidelinks}` for clickable but invisible links.
  - Real text (no `\textsc` ligatures that confuse parsers), `pdfa-1b` output.
  - Latin Modern / Inter fallback, 10–11pt body, 1.15 line spacing,
    consistent 0.6in margins, section spacing from token scale.
- **Pipeline**: `validate(payload) → render(j2 → .tex) → tectonic compile →
  upload to R2 (key resumes/<user>/<resume_id>.pdf) → store hash + size → return
  presigned URL (15 min TTL)`. Idempotency via content-hash so re-clicking
  *Download PDF* on unchanged data is a cache hit, not a recompile.
- **Validation**: payload runs through a Pydantic model; LaTeX-unsafe chars
  (`& % $ # _ { } ~ ^ \`) escaped at template-render time; max sizes per
  field enforced server-side. Templates are read-only artifacts shipped with
  the image — users never supply LaTeX directly (no command injection).
- **Pro gating**: free tier limited to 1 export / day; Pro unlimited.
  Wires through the existing `require_plan(Plan.PRO, feature=…)` dependency
  with a quota counter rather than a hard block on Free.

**Dependencies / prerequisites**

- v1.2.4 pagination (lists growing).
- Build artifact: Celery worker Docker image bundles Tectonic + cached font
  bundle. Adds ~120 MB to the worker image.
- Migrations: `resume_exports` table (id, resume_id, user_id, content_hash,
  s3_key, file_size, template_id, created_at).

**Expected outcomes**

- Median render time < 4 s on cold cache, < 200 ms on warm cache.
- Same source data → byte-identical PDF (deterministic build via fixed
  Tectonic revision + pinned font bundle).
- Affinda parser correctly extracts ≥ 90% of fields on the Modern template.

**Risks**

- LaTeX compile failures from edge-case user input (curly quotes inside
  achievements, RTL characters). Mitigation: aggressive escape + a curated
  Unicode allowlist, with a fallback "plain renderer" path that produces a
  no-LaTeX PDF via ReportLab on compile error.
- Worker image bloat. Mitigation: multi-stage build, font cache as a
  read-only Railway volume.

### v3.0 — Platform + Stability Backlog

v3.0 splits into **two parallel tracks**: the original Platform work
(public API, SSO, white-label) and a Stability Backlog that absorbs
the bug-hunt findings + UX asks. Stability tickets ship first; the
Platform tier ramps up once the foundation is clean.

#### Track A — Stability Backlog (ship first, ordered by user impact)

| # | ID | Severity | Area | Title |
|---|---|---|---|---|
| 1 | UX-01 | High | Frontend | Remove the violet underline beneath "a portfolio that gets you hired" (Hero) |
| 2 | UX-02 | High | Frontend | "Three themes" section heading is invisible (low contrast) |
| 3 | UX-03 | High | Frontend | Resume builder is stuck at the Projects step (~50%) — cannot advance |
| 4 | UX-04 | High | Frontend | "Build portfolio" CTA does not produce a website |
| 5 | AI-01 | High | Backend | Replace Claude/Anthropic with a free, no-card-required AI provider (e.g. OpenRouter free models, Groq free tier, Together free tier) |
| 6 | B5 | Critical | Frontend | Builder live-preview iframe always 404s — points at `/portfolio/p/<UUID>` instead of `/portfolio/p/<slug>` |
| 7 | B1 | Critical | DB | Backfill migration 0007 produces wrong memberships — CTE joins on `stripe_customer_id` which is NULL for all free users; rewrite to carry `user_id` through |
| 8 | B10 | Critical | Backend | Stripe webhook only updates `User.plan`; must also flip `Organization.plan` / `stripe_subscription_id` so org members lose Pro on cancellation |
| 9 | B2 | Critical | Backend | `require_role` opens a second DB session via `async for db in get_db()` — should accept the request session as a dependency |
| 10 | UX-05 | Medium | Frontend | UI/UX color polish — improve overall palette contrast + accent richness across landing, dashboard, builder |
| 11 | B18 | High | Backend | LaTeX bullet separator in skills list gets clobbered — Jinja `finalize=latex_escape` re-escapes the join separator's backslashes |
| 12 | B6 | High | Frontend | `OnboardingChecklist` mutates `localStorage` during render — move to `useEffect`, also call `setDismissed(true)` so it self-dismisses |
| 13 | B9 | High | Backend | ReportLab `Paragraph(f"<b>{name}</b>", ...)` interprets `<`, `>`, `&` in user input as XML — escape every f-string argument |
| 14 | B8 | High | Frontend | `usePreviewBridge` returns `ready` from a ref → never re-renders consumers; promote to React state |
| 15 | B12/B22 | High | Backend+Frontend | Audit-log page shows random org's logs across refreshes — `list_organizations` returns unordered; frontend picks `orgs[0]` blindly |
| 16 | B11 | High | Backend | Marketplace submit has a TOCTOU window on duplicate template id — catch `IntegrityError` and return 409 instead of letting it 500 |
| 17 | B4 | Medium | Backend | Org members can't see org-owned resources — `_get_portfolio_or_404` / `_get_resume_or_404` still gate purely on `user_id`. Org-aware ownership policy needed for v2.0's RBAC to actually work |
| 18 | B17 | Medium | Frontend | Service worker `caches.match(SHELL_URL)` resolves to `undefined` when install missed; `respondWith(undefined)` becomes a network error — fall back to a hardcoded `Response` |
| 19 | B3 | Medium | Backend | `remove_member` has a dead `owner_count` variable + a redundant second query — collapse to a single `func.count()` scalar |
| 20 | B13/B21 | Medium | Backend | Marketplace `submit_template` overloads `is_pro = price_cents > 0`. Separate concepts: "requires Pro plan" vs "paid template" |
| 21 | B7 | Medium | Frontend | `ThemeContext.test.tsx` still tests `setMode("dark")` which is now a no-op — delete or rewrite the tests |
| 22 | B23 | Medium | Frontend | `useDebouncedSave` cleanup fires on every flush change, not just unmount — split the effect into save-on-unmount-only |
| 23 | B14 | Medium | Backend | `record_audit_safe` doesn't commit — caller must commit. Wrapper name is misleading |
| 24 | B16 | Medium | Backend | Public viewer `p.views += 1` race-conditions on concurrent reads — switch to `UPDATE … SET views = views + 1` atomic |
| 25 | B19 | Low | Frontend | Hero CTA `bg-[var(--pf-cta-warm, var(--pf-accent))]` fallback never fires under Aurora palette — Aurora users get unstyled bg |
| 26 | B20 | Low | Backend+Frontend | Marketplace `rating_average` serialized as Decimal/string by Pydantic v2 — normalize to number server-side |
| 27 | B24 | Low | Frontend | Repetitive `@fastify/otel` import-in-the-middle warnings flood the dev-server log on every compile |
| 28 | B25 | Low | Backend | Defensive `getattr(current_user, "stripe_account_id", None)` is misleading after migration 0011 |
| 29 | B26 | Low | Backend | LaTeX template uses `{% if links.linkedin %}` under `StrictUndefined` — passing an empty dict raises on missing key access |
| 30 | B27 | Low | Frontend | i18n quote-mark consistency — en.json uses straight apostrophes, Spanish curly, Hindi none |

Suggested batching for execution:

  **Sprint 3.0.S1 — User-blocking fixes** (1, 2, 3, 4, 5, 6)
  **Sprint 3.0.S2 — Data integrity** (7, 8, 9, 15, 17)
  **Sprint 3.0.S3 — Render correctness** (11, 13, 24, 16, 29)
  **Sprint 3.0.S4 — UI/UX polish** (10, 12, 14, 22, 25)
  **Sprint 3.0.S5 — Cleanup** (18, 19, 20, 21, 23, 26, 27, 28, 30)

#### Track B — Platform tier (after Stability passes)

v3.0.0 public REST API + keys · v3.0.1 outbound webhooks · v3.0.2 OAuth2 third-party apps · v3.0.3 white-label · v3.0.4 SOC 2 controls · v3.0.5 SSO/SAML

#### AI provider research note (for AI-01)

Candidate free-tier providers that don't require a credit card:

| Provider | Free quota | Notes |
|---|---|---|
| **OpenRouter (free models)** | Generous; rotates models | Already integrated as fallback in v1.2.2. Promote to primary. |
| **Groq Cloud** | ~30 req/min on Llama-3.3-70B | No card; fastest tokens/sec on the market. |
| **Google AI Studio (Gemini Flash)** | 15 RPM / 1M tokens/day | No card for Studio tier. Quality decent, latency low. |
| **Together AI** | Free tier with rate limits | Llama-3.x models. |
| **Cerebras Cloud** | Free tier | Very fast Llama. |

Recommended migration: drop Anthropic from the failover chain when
no `ANTHROPIC_API_KEY` is set; promote OpenRouter free model to
primary, add Groq as the new fallback. Zero card requirement,
unchanged response shape (OpenAI-compatible).

---

## 🧰 Development Workflow

### Branching — *Trunk-based with short-lived release branches*

```
main                ← always deployable, protected
├── release/v1.x    ← cut at start of a minor; only fixes merged
├── feat/<slug>     ← short-lived (<3 days), squash-merge to main
├── fix/<slug>      ← bugfix branches
├── chore/<slug>    ← deps, infra, docs
└── hotfix/<slug>   ← from tag, merged to main + release/*
```

### Commit Convention — *Conventional Commits*

```
<type>(<scope>): <subject>

types: feat | fix | chore | docs | refactor | perf | test | build | ci | security | revert
scopes: frontend | backend | db | auth | billing | ai | infra | ui | a11y | deps
```

Example: `feat(auth): enable email + phone OTP via clerk`

### Pull Request Requirements

- Linked issue + version label (e.g. `v1.1`)
- Description: **What / Why / How / Test plan / Screenshots**
- Checklist: tests added · types pass · lint clean · a11y unchanged · docs updated
- **2 approvals** for `feat`/`security`; **1 approval** for `fix`/`chore`
- All CI status checks green
- Rebase if branch is > 10 commits behind `main`

### Quality Gates (required CI checks)

1. `lint` — ruff + black + isort + eslint + prettier
2. `typecheck` — mypy + `tsc --noEmit`
3. `test-backend` — pytest with coverage gate
4. `test-frontend` — vitest with coverage gate
5. `e2e` — Playwright smoke suite
6. `a11y` — axe-core
7. `lighthouse-ci` — perf/SEO/a11y budgets
8. `security-scan` — Trivy + npm audit + pip-audit
9. `openapi-diff` — breaking API changes require `!` in commit

### Sub-Version Review Gate (mandatory before tag)

| Step | Owner | Pass criteria |
|---|---|---|
| 1. Scope review | Tech lead | All listed deliverables present |
| 2. Architecture review | Architect | Implementation matches ADRs |
| 3. Code review | 2 reviewers | All comments resolved |
| 4. Test review | QA | Coverage ≥ gate; no skipped tests |
| 5. Performance check | Eng | p95 API < 300ms; LCP < 2.5s |
| 6. Regression sweep | QA | Full Playwright suite green |
| 7. Security review | Security | Scans clean; new endpoints rate-limited & authz-tested |
| 8. Docs update | Author | README / CHANGELOG / ADR updated |
| 9. Manual QA | PM | Acceptance script passes on staging |
| 10. Sign-off | Release manager | Approve → tag |

### Release Procedure

```bash
# 1. bump versions + changelog
npm version --no-git-tag-version <ver> -w frontend
# bump backend pyproject.toml + update CHANGELOG.md

# 2. commit
git commit -m "chore(release): v1.1.0"

# 3. annotated, signed tag
git tag -s v1.1.0 -m "VyroPortify v1.1.0 — Foundation & Stability"

# 4. push
git push origin main --follow-tags

# 5. GitHub release
gh release create v1.1.0 --notes-from-tag

# 6. Deploy: staging → smoke → prod canary 10% → 100%
```

### Rollback

- **DB** — every migration has a tested down-migration OR documented forward-fix.
- **Backend** — Railway redeploy previous image digest.
- **Frontend** — Vercel promote previous deployment instantly.
- **Feature flags** — risky features behind a flag; kill-switch first, redeploy second.
- **DNS** — TTL ≤ 300s during rollouts.

### Post-Release Verification

- **T+0** — synthetic check: signup → upload → generate → publish on prod
- **T+1h** — Sentry error rate ≤ baseline; p95 latency ≤ baseline
- **T+24h** — PostHog funnel parity; no new Sentry spikes; cost dashboard normal

### Coverage Targets by Version

| Version | BE | FE | E2E | A11y | Lighthouse |
|---|---|---|---|---|---|
| v1.0 | 70% | 50% | smoke | optional | optional |
| v1.1 | 80% | 55% | + auth/billing | warn | warn |
| v1.2 | 80% | 60% | + email/domain | warn | warn |
| v1.3 | 80% | 70% | + visual diff | **gate** | **gate** |
| v1.4 | 80% | 75% | + kbd/cmd-K | gate | gate |
| v1.5 | 85% | 80% | + perf script | gate | gate |
| v1.6 | 85% | 80% | full | gate | gate |
| v2.0 | 90% (billing 95%) | 80% | + multi-tenant | gate | gate |

### Feature-Creep Controls

1. **One version label per PR** — must match an open milestone.
2. **Scope-lock** — when a sub-version branch is cut, scope freezes.
3. **WIP limit** — max 3 open `feat/*` branches per sub-version.
4. **Definition of Done** posted on every sub-version issue.
5. **No drive-by refactors** — require a separate `refactor/*` PR.
6. **Deprecation policy** — public-surface removal needs one minor-version notice.

### Per-Release Checklist

```
[ ] All sub-version deliverables shipped
[ ] CHANGELOG.md updated
[ ] ADRs added/updated
[ ] OpenAPI diff reviewed
[ ] Migrations have down-paths or forward-fix doc
[ ] Feature flags configured + default state set
[ ] Lighthouse + axe gates green
[ ] Security scans clean
[ ] Coverage ≥ version target
[ ] Manual QA script signed off (PM)
[ ] Staging smoke green for 24h
[ ] Rollback plan documented
[ ] Tag created + signed
[ ] Release notes published
[ ] T+0 / T+1h / T+24h verification complete
```

---

## 📄 License

MIT © 2025 [Gaurav06120714](https://github.com/Gaurav06120714)
