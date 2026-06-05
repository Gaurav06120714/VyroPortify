from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "VyroPortify"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False  # NEVER default True — set DEBUG=True explicitly in dev .env only

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/vyroportify"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO_SQL: bool = False  # set True to log all SQL

    # ── Security / JWT ────────────────────────────────────────────────────
    SECRET_KEY: str = "changeme-use-at-least-32-random-chars-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24          # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30    # 30 days
    ALGORITHM: str = "HS256"

    # ── CORS ──────────────────────────────────────────────────────────────
    # Dev defaults match the ports the project actually uses (Next dev
    # server runs on 3007 per README; 3000/3001 retained for legacy /
    # parallel-instance setups). Override in prod via env.
    CORS_ORIGINS: list[str] = [
        "http://localhost:3007",
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── External services ─────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""          # price_xxx from Stripe dashboard
    STRIPE_PRO_PRODUCT_ID: str = ""        # prod_xxx (used for feature gating)
    FRONTEND_URL: str = "http://localhost:3000"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    # Google AI Studio (Gemini) — free tier, no credit card required.
    # Promoted to primary provider in ai_client (v3 AI-01 ticket).
    GEMINI_API_KEY: str = ""

    # ── Clerk (authentication) ────────────────────────────────────────────
    # Format: https://<your-clerk-subdomain>.clerk.accounts.dev/.well-known/jwks.json
    # Do NOT hardcode this — your subdomain identifies your Clerk instance.
    CLERK_JWKS_URL: str = ""
    # Signing secret for Clerk webhooks (Settings → Webhooks → Signing Secret).
    # Required for /api/v1/auth/clerk-webhook signature verification (v3.4.0).
    CLERK_WEBHOOK_SECRET: str = ""

    # ── Storage — AWS S3 or Cloudflare R2 (same boto3 interface) ─────────
    # Provider selection: "s3" | "r2"
    STORAGE_PROVIDER: str = "s3"

    # AWS S3 credentials (also used as fallback for R2 key/secret)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""

    # Cloudflare R2 — only needed when STORAGE_PROVIDER="r2"
    # endpoint format: https://<account_id>.r2.cloudflarestorage.com
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""

    # Presigned URL lifetime constraints
    PRESIGNED_URL_DEFAULT_HOURS: int = 24   # used when no ttl_hours specified
    PRESIGNED_URL_MAX_HOURS: int = 168       # 7 days hard ceiling

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 5

    # ── Transactional email (Resend) ───────────────────────────────────────────
    # Leave RESEND_API_KEY empty in dev — the email service no-ops silently so
    # local flows are not blocked. In production, treat empty as a misconfig
    # (logged but non-fatal so a Resend outage doesn't break paid checkouts).
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "VyroPortify <noreply@vyroportify.com>"

    @property
    def storage_bucket(self) -> str:
        """Active bucket name — R2 takes precedence when provider is r2."""
        return self.R2_BUCKET if self.STORAGE_PROVIDER == "r2" else self.AWS_S3_BUCKET

    @property
    def storage_endpoint_url(self) -> str | None:
        """endpoint_url for boto3 — None for AWS S3 (uses default), set for R2."""
        return self.R2_ENDPOINT_URL if self.STORAGE_PROVIDER == "r2" else None

    @property
    def storage_access_key_id(self) -> str:
        return self.R2_ACCESS_KEY_ID if self.STORAGE_PROVIDER == "r2" else self.AWS_ACCESS_KEY_ID

    @property
    def storage_secret_access_key(self) -> str:
        return self.R2_SECRET_ACCESS_KEY if self.STORAGE_PROVIDER == "r2" else self.AWS_SECRET_ACCESS_KEY

    @property
    def storage_region(self) -> str:
        # R2 requires "auto" as region; S3 uses the configured region
        return "auto" if self.STORAGE_PROVIDER == "r2" else self.AWS_REGION

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v == "changeme-use-at-least-32-random-chars-in-production":
            return v   # allow default in dev; warn at startup instead
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()


# ── Production validation ──────────────────────────────────────────────────────

def validate_production_config() -> None:
    """Validate critical configuration values at startup.

    This function is called in main.py's on_startup() handler so the server
    fails fast with a clear error message rather than silently running in an
    insecure or broken state.

    In development / staging, misconfigurations are logged as warnings.
    In production, they raise RuntimeError to halt the server.

    Checks:
      1. SECRET_KEY must not be the default dev placeholder.
      2. ANTHROPIC_API_KEY must be set (Claude is core to the product).
      3. DATABASE_URL must be set and not the default placeholder.
      4. CORS_ORIGINS must be non-empty so CORS doesn't default to permissive.
    """
    import logging as _logging

    log = _logging.getLogger(__name__)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. SECRET_KEY — default value is publicly known; using it in prod means
    #    anyone who reads our repo can forge JWTs / session cookies.
    _DEFAULT_KEY = "changeme-use-at-least-32-random-chars-in-production"
    if settings.SECRET_KEY == _DEFAULT_KEY:
        msg = "SECRET_KEY is the default dev placeholder — rotate it immediately"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 2. OPENROUTER_API_KEY — required for AI features (replaced Anthropic).
    if not settings.OPENROUTER_API_KEY and not settings.ANTHROPIC_API_KEY:
        msg = "Neither OPENROUTER_API_KEY nor ANTHROPIC_API_KEY is set — AI features will fail"
        warnings.append(msg)

    # 3. DATABASE_URL — the default value points to localhost which won't work
    #    in any containerised or cloud environment.
    _DEFAULT_DB = "postgresql+asyncpg://user:password@localhost:5432/vyroportify"
    if not settings.DATABASE_URL or settings.DATABASE_URL == _DEFAULT_DB:
        msg = "DATABASE_URL is missing or still the default dev value"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 4. CORS_ORIGINS — an empty list causes FastAPI's CORSMiddleware to deny
    #    all cross-origin requests, breaking the frontend completely.
    if not settings.CORS_ORIGINS:
        msg = "CORS_ORIGINS is empty — all browser requests will be blocked by CORS"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 5. CLERK_JWKS_URL — required for JWT verification; empty means all requests
    #    will fail auth. Also validates it's not a placeholder.
    if not settings.CLERK_JWKS_URL:
        msg = "CLERK_JWKS_URL is not set — authentication will be broken"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 6. DEBUG must be False in production — True leaks stack traces to clients.
    if settings.DEBUG and settings.is_production:
        errors.append("DEBUG=True is not allowed in production — set DEBUG=False")

    # Emit warnings for dev/staging
    for w in warnings:
        log.warning("CONFIG WARNING: %s", w)

    # Fail hard in production
    if errors:
        error_list = "\n  - ".join(errors)
        raise RuntimeError(
            f"Production startup blocked — fix these configuration errors:\n  - {error_list}"
        )
