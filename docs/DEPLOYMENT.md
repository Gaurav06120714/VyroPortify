# Deployment

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

