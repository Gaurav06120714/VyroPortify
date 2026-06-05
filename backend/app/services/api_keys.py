"""API key generation, hashing, and verification (v3.0.0)."""

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User

KEY_PREFIX = "vp_"
RAW_LEN = 32  # url-safe characters of randomness


def generate_raw_key() -> str:
    """Return a freshly generated key string in the form vp_<32 url-safe chars>."""
    return KEY_PREFIX + secrets.token_urlsafe(RAW_LEN)[:RAW_LEN]


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def display_prefix(raw: str) -> str:
    # e.g. "vp_AbCdEfGh" — first 8 chars after the vp_ prefix
    body = raw[len(KEY_PREFIX) :]
    return KEY_PREFIX + body[:8]


class APIKeyAuth:
    """Resolved API key auth context — the user plus the granted scope list."""

    def __init__(self, user: User, key: APIKey):
        self.user = user
        self.key = key
        self.scopes = key.scope_list()

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope: {scope}",
            )


async def get_api_key_auth(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> APIKeyAuth:
    """FastAPI dependency: validate a `Authorization: Bearer vp_…` API key."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raw = authorization.split(" ", 1)[1].strip()
    if not raw.startswith(KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    key_hash = hash_key(raw)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    now = datetime.now(timezone.utc)
    if not key.is_active(now):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key revoked or expired")

    user = await db.get(User, key.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner missing")

    key.last_used_at = now
    await db.flush()
    return APIKeyAuth(user=user, key=key)


def require_scope(scope: str):
    """Dependency factory: 403 unless the calling API key has `scope`."""

    async def _dep(auth: APIKeyAuth = Depends(get_api_key_auth)) -> APIKeyAuth:
        auth.require_scope(scope)
        return auth

    return _dep
