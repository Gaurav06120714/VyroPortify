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

VyroPortify uses Claude AI to transform your resume — or a quick guided form — into a beautiful, public portfolio website. Hosted instantly, no code required.

| Feature | Free | Pro ($9/mo) |
|---|:---:|:---:|
| AI Resume Builder (12-step guided) | ✅ | ✅ |
| Portfolio templates | 1 | All 4 |
| Portfolios | 3 | Unlimited |
| AI skill suggestions | ❌ | ✅ |
| AI cover letter generator | ❌ | ✅ |
| Custom domain | ❌ | ✅ |
| Public URL (`/portfolio/your-name`) | ✅ | ✅ |
| Bulk ZIP export | 2/day | 20/day |

### Templates

| Template | Style | Best For |
|---|---|---|
| **Aurora** | Dark electric, animated gradient | Developers & Designers |
| **Minimal** | Clean white, typography-first | PMs & Researchers |
| **Cyber** | Neon glassmorphism, terminal feel | Anyone who refuses to blend in |
| **Executive** | Two-column serif, gold accents | Senior Engineers & Managers |

### Platform capabilities (v3.x)

| Surface | What it does |
|---|---|
| **Public REST API** | `/api/v1/public/*` — scoped API keys (`vp_…`) for third-party integrations |
| **Outbound webhooks** | HMAC-signed events (`portfolio.published`, `subscription.changed`, …) with retry + replay |
| **OAuth 2.0** | Authorization-code + PKCE for third-party apps requesting access on a user's behalf |
| **White-label** | Per-org logo, colors, custom CSS — applied to every published portfolio (enterprise) |
| **SSO / SAML** | Per-org IdP config + email-domain discovery (enterprise) |
| **Admin analytics** | Overview, time-series, top portfolios — org-scoped |
| **Compliance** | Right-to-access export, right-to-erasure, audit trail, policy disclosure |
| **Bulk export** | Streaming ZIP of every portfolio the user owns, with JSON manifest |

---

## 🛡 Application Security

VyroPortify treats abuse-resistance as a first-class feature, not an afterthought.
Defences are layered so a single failure — a CDN outage, a leaked credential,
a misbehaving receiver — cannot take the platform down.

### Authentication & authorization

| Concern | Implementation |
|---|---|
| User auth | Clerk JWTs (RS256), verified against the cached JWKS |
| Password / Email-OTP / Google / GitHub login | Clerk hosted UI — config in [`docs/AUTH_SETUP.md`](docs/AUTH_SETUP.md) |
| User mirror | Svix-signed `/api/v1/auth/clerk-webhook` writes every signup into the DB |
| Service-to-service auth | Personal API keys (`vp_…`), SHA-256 hashed at rest, scoped permissions |
| Third-party apps | OAuth 2.0 authorization-code flow with PKCE (S256), `oat_…` access tokens |
| RBAC | Per-org `owner / admin / editor / viewer`, enforced by `require_role` dependency |
| SSO (enterprise) | Per-org SAML config with email-domain discovery (`/api/v1/sso/login`) |

### Layered DDoS / abuse defences

| Layer | Mechanism |
|---|---|
| **L3/L4 floods** | Cloudflare proxy + WAF + Bot Fight Mode (operator-configured) |
| **L7 scanner probes** | Middleware drops `/.env`, `/.git/`, `/wp-admin`, etc. → instant 404 |
| **Headless bots** | Empty / `<3`-char `User-Agent` rejected on `POST/PUT/PATCH/DELETE` |
| **Per-IP rate limit** | SlowAPI + Redis, proxy-aware key fn extracts `CF-Connecting-IP` |
| **Per-account daily quota** | Plan-aware Redis counters, expire at UTC midnight |
| **Receiver amplification** | Outbound webhooks capped at 60 deliveries / endpoint / minute |
| **OAuth brute-force** | `/oauth/token` rate-limited to 20/min |
| **Oversized payloads** | Pre-handler size check against `MAX_REQUEST_BODY_BYTES` |
| **Static-asset spikes** | Public portfolios set `Cache-Control: public, max-age=300, s-maxage=900` |
| **Prompt injection** | All user-supplied strings normalised through `sanitize_for_ai` before the model |
| **Signature replay** | Webhook header `X-VyroPortify-Signature: t=<unix>,v1=<hmac>`; ±5 min window |

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
| `GET /api/v1/compliance/policies` | Public retention + subprocessor disclosure |
| `GET /api/v1/compliance/me/export` | Article 15 right-to-access export |
| `DELETE /api/v1/compliance/me` | Article 17 right-to-erasure with cascaded cleanup |
| `GET /api/v1/compliance/me/audit` | Caller-scoped audit-event history |
| `GET /api/v1/admin/users.csv` / `.xlsx` | Owner-gated export of all registered users |

### Operational playbook

A full DDoS playbook lives in **[`docs/DDOS_HARDENING.md`](docs/DDOS_HARDENING.md)**:
Cloudflare onboarding, Cloudflare Turnstile (CAPTCHA) wiring, nginx limits,
autoscale caps, Sentry alert thresholds, and an incident-response runbook.

---

## 📚 Documentation

The rest of the documentation lives under [`docs/`](docs/):

| Topic | File |
|---|---|
| 🔐 Authentication methods (password, OTP, Google, GitHub) | [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) |
| 🔐 Clerk dashboard setup (step-by-step) | [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md) |
| 🚀 Local development (env, services, migrations) | [docs/LOCAL_DEV.md](docs/LOCAL_DEV.md) |
| 🗂 Project structure | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) |
| 🔑 API reference (full v3 surface) | [docs/API.md](docs/API.md) |
| 🌐 Deployment (Vercel + Railway) | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| 🧪 Testing (vitest, pytest, Playwright) | [docs/TESTING.md](docs/TESTING.md) |
| 🛡 DDoS hardening playbook | [docs/DDOS_HARDENING.md](docs/DDOS_HARDENING.md) |
| 💾 Backup & disaster recovery | [docs/BACKUP_DR.md](docs/BACKUP_DR.md) |
| 📖 Operational runbook | [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| 🎨 Theme system | [docs/THEME.md](docs/THEME.md) |
| 🗺 Roadmap & development workflow | [docs/ROADMAP_AND_WORKFLOW.md](docs/ROADMAP_AND_WORKFLOW.md) |

---

## 🚀 Recently Shipped

| Tag | Theme |
|---|---|
| [`v3.0.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.0) | Public REST API + scoped personal API keys |
| [`v3.0.1`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.1) | Outbound webhooks — HMAC-signed, retried |
| [`v3.0.2`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.2) | OAuth 2.0 (authorization-code + PKCE) |
| [`v3.0.3`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.3) | White-label / custom theme for enterprise |
| [`v3.0.4`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.4) | SOC 2 / GDPR endpoints |
| [`v3.0.5`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.0.5) | SSO / SAML foundation |
| [`v3.1.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.1.0) | Admin analytics API |
| [`v3.2.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.2.0) | Bulk portfolio export as ZIP |
| [`v3.3.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.3.0) | Webhook event catalog + replay |
| [`v3.3.1`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.3.1) | DDoS hardening (quotas, middleware, throttles) |
| [`v3.4.0`](https://github.com/Gaurav06120714/VyroPortify/releases/tag/v3.4.0) | Clerk-backed multi-method auth + user export |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

Made with ⚡ by [Gaurav06120714](https://github.com/Gaurav06120714).
