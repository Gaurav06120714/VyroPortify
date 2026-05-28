"""Clerk JWT verification and current-user resolution.

The frontend uses Clerk for auth and sends Clerk-issued JWTs as Bearer tokens.
We verify those tokens against Clerk's JWKS endpoint (RS256) and then look up
(or auto-create) the corresponding User row in our database.

Legacy password-auth helpers (hash_password, verify_password, create_access_token,
create_refresh_token) have been fully removed because:
  - They raised NotImplementedError — dead code that pentesters could abuse.
  - Importing bcrypt at startup wastes memory and increases attack surface.
  - Clerk handles all credential management; we never issue our own tokens.
"""

import logging
import time
from typing import TYPE_CHECKING, Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import Plan
from app.database import get_db

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_BEARER = HTTPBearer(auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# ── JWKS cache ─────────────────────────────────────────────────────────────────
# Clerk's JWKS is stable (rotates rarely). We cache it for 1 hour so we don't
# make an outbound HTTP call on every authenticated request, while still picking
# up key rotations within a reasonable window.

_JWKS_CACHE: dict[str, Any] = {}
_JWKS_FETCHED_AT: float = 0.0
_JWKS_TTL = 3600  # seconds

CLERK_JWKS_URL = settings.CLERK_JWKS_URL  # set via CLERK_JWKS_URL env var

if not CLERK_JWKS_URL:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "CLERK_JWKS_URL is not set — all authenticated requests will fail. "
        "Set CLERK_JWKS_URL in your .env file."
    )


async def _get_jwks() -> dict[str, Any]:
    """Fetch/refresh Clerk's JSON Web Key Set (cached for 1hr)."""
    global _JWKS_CACHE, _JWKS_FETCHED_AT

    now = time.time()
    if _JWKS_CACHE and (now - _JWKS_FETCHED_AT < 3600):
        return _JWKS_CACHE

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(CLERK_JWKS_URL, timeout=5)
            resp.raise_for_status()
            _JWKS_CACHE = resp.json()
            _JWKS_FETCHED_AT = now
            logger.debug("Clerk JWKS refreshed — %d key(s)", len(_JWKS_CACHE.get("keys", [])))
    except Exception as exc:
        logger.error("Failed to fetch Clerk JWKS: %s", exc)
        if not _JWKS_CACHE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service temporarily unavailable",
            )
    return _JWKS_CACHE


async def verify_clerk_token(token: str) -> dict[str, Any]:
    """Verify a Clerk-issued JWT and return its payload.

    Raises HTTPException 401 on any failure.
    """
    jwks = await _get_jwks()

    try:
        # jose automatically selects the key matching the 'kid' header
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't set 'aud' by default
        )
    except JWTError as exc:
        logger.debug("Clerk JWT verification failed: %s", exc)
        # Log auth failures for security monitoring — no PII in the log
        from app.core.audit_log import log_security_event
        log_security_event(
            "auth_failure",
            user_id=None,
            detail={"reason": "jwt_verification_failed", "error": str(exc)[:200]},
        )
        raise _CREDENTIALS_EXCEPTION

    # Clerk puts the user ID in 'sub'
    if not payload.get("sub"):
        raise _CREDENTIALS_EXCEPTION

    return payload


# ── FastAPI dependency: current authenticated user ─────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_BEARER)],
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Resolve a Clerk Bearer token → User ORM row (auto-creates on first visit).

    Raises HTTP 401 for invalid/expired tokens.
    """
    from app.models.user import User  # noqa: PLC0415

    payload = await verify_clerk_token(credentials.credentials)
    clerk_id: str = payload["sub"]

    # Look up by clerk_user_id
    result = await db.execute(select(User).where(User.clerk_user_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Auto-create the user on first API call after sign-up.
        # We deliberately do NOT log the email address here to avoid PII in logs
        # (audit_log.py handles structured security events separately).
        email = (
            payload.get("email")
            or (payload.get("email_addresses") or [{}])[0].get("email_address", "")
            or f"{clerk_id}@clerk.local"
        )
        name = (
            f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
            or payload.get("username")
            or None
        )
        user = User(
            clerk_user_id=clerk_id,
            email=email,
            name=name,
            plan=Plan.FREE,
        )
        db.add(user)
        await db.flush()
        logger.info("Auto-created user clerk_id=%s", clerk_id)  # no email in logs — PII

    return user


# Annotated shorthand for route signatures:
#   async def protected(current_user: CurrentUser) -> ...:
CurrentUser = Annotated[Any, Depends(get_current_user)]
