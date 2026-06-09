"""Centralized security configuration for VyroPortify.

All security-relevant constants and constraints live here so they can be:
  1. Loaded from environment variables (production-grade, 12-factor).
  2. Changed in one place without hunting through router/service files.
  3. Audited independently by security reviewers.

Import pattern:
    from app.core.security_config import security_settings
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class SecuritySettings(BaseSettings):
    """Security-specific settings loaded from environment variables.

    These supplement the main Settings class and are focused exclusively on
    security boundaries, limits, and policies.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    MAX_REQUEST_BODY_BYTES: int = 10 * 1024 * 1024   
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024           

    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    MAX_TEXT_LENGTH_FOR_AI: int = 50_000  

    RATE_LIMIT_AI_ENDPOINTS: str = "10/hour"      
    RATE_LIMIT_DEFAULT: str = "200/minute"        

    CORS_ORIGINS_PRODUCTION: list[str] = []

    WEBHOOK_IDEMPOTENCY_TTL_SECONDS: int = 86_400  

    CONTENT_SECURITY_POLICY: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://clerk.accounts.dev https://*.clerk.accounts.dev; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://img.clerk.com https://images.clerk.dev "
        "https://avatars.githubusercontent.com https://lh3.googleusercontent.com "
        "https://*.amazonaws.com; "
        "connect-src 'self' https://api.clerk.dev https://*.clerk.accounts.dev "
        "https://api.anthropic.com https://api.stripe.com; "
        "font-src 'self' data:; "
        "frame-src 'none'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    @field_validator("MAX_TEXT_LENGTH_FOR_AI")
    @classmethod
    def validate_ai_limit(cls, v: int) -> int:
        if v < 1000:
            raise ValueError("MAX_TEXT_LENGTH_FOR_AI must be at least 1000 chars")
        if v > 500_000:
            raise ValueError("MAX_TEXT_LENGTH_FOR_AI cannot exceed 500,000 chars")
        return v

security_settings = SecuritySettings()
