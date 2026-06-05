# Roadmap And Workflow

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

