from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "VyroPortify"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  
    DEBUG: bool = False  

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/vyroportify"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO_SQL: bool = False  

    SECRET_KEY: str = "changeme-use-at-least-32-random-chars-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24          
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30    
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3007",
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""          
    STRIPE_PRO_PRODUCT_ID: str = ""        
    FRONTEND_URL: str = "http://localhost:3000"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    GEMINI_API_KEY: str = ""

    CLERK_JWKS_URL: str = ""
    
    CLERK_WEBHOOK_SECRET: str = ""

    STORAGE_PROVIDER: str = "s3"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""

    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""

    PRESIGNED_URL_DEFAULT_HOURS: int = 24   
    PRESIGNED_URL_MAX_HOURS: int = 168       

    MAX_UPLOAD_SIZE_MB: int = 5

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
        
        return "auto" if self.STORAGE_PROVIDER == "r2" else self.AWS_REGION

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v == "changeme-use-at-least-32-random-chars-in-production":
            return v   
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

settings = Settings()

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

    _DEFAULT_KEY = "changeme-use-at-least-32-random-chars-in-production"
    if settings.SECRET_KEY == _DEFAULT_KEY:
        msg = "SECRET_KEY is the default dev placeholder — rotate it immediately"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    if not settings.OPENROUTER_API_KEY and not settings.ANTHROPIC_API_KEY:
        msg = "Neither OPENROUTER_API_KEY nor ANTHROPIC_API_KEY is set — AI features will fail"
        warnings.append(msg)

    _DEFAULT_DB = "postgresql+asyncpg://user:password@localhost:5432/vyroportify"
    if not settings.DATABASE_URL or settings.DATABASE_URL == _DEFAULT_DB:
        msg = "DATABASE_URL is missing or still the default dev value"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    if not settings.CORS_ORIGINS:
        msg = "CORS_ORIGINS is empty — all browser requests will be blocked by CORS"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    if not settings.CLERK_JWKS_URL:
        msg = "CLERK_JWKS_URL is not set — authentication will be broken"
        if settings.is_production:
            errors.append(msg)
        else:
            warnings.append(msg)

    if settings.DEBUG and settings.is_production:
        errors.append("DEBUG=True is not allowed in production — set DEBUG=False")

    for w in warnings:
        log.warning("CONFIG WARNING: %s", w)

    if errors:
        error_list = "\n  - ".join(errors)
        raise RuntimeError(
            f"Production startup blocked — fix these configuration errors:\n  - {error_list}"
        )
