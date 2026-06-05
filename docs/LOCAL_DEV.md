# Local Dev

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

