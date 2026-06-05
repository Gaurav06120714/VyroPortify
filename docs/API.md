# Api

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

