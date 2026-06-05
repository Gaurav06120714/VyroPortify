# Project Structure

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

