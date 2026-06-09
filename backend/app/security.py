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

_JWKS_CACHE: dict[str, Any] = {}
_JWKS_FETCHED_AT: float = 0.0
_JWKS_TTL = 3600  

CLERK_JWKS_URL = settings.CLERK_JWKS_URL  

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
        
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},  
        )
    except JWTError as exc:
        logger.debug("Clerk JWT verification failed: %s", exc)
        
        from app.core.audit_log import log_security_event
        log_security_event(
            "auth_failure",
            user_id=None,
            detail={"reason": "jwt_verification_failed", "error": str(exc)[:200]},
        )
        raise _CREDENTIALS_EXCEPTION

    if not payload.get("sub"):
        raise _CREDENTIALS_EXCEPTION

    return payload

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_BEARER)],
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Resolve a Clerk Bearer token → User ORM row (auto-creates on first visit).

    Raises HTTP 401 for invalid/expired tokens.
    """
    from app.models.user import User  

    payload = await verify_clerk_token(credentials.credentials)
    clerk_id: str = payload["sub"]

    result = await db.execute(select(User).where(User.clerk_user_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        
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
        logger.info("Auto-created user clerk_id=%s", clerk_id)  

        from app.models.organization import Membership, Organization

        owner_label = name or (email.split("@")[0] if email else None)
        org_name = f"{owner_label}’s Workspace" if owner_label else "Personal Workspace"
        org = Organization(
            name=org_name,
            slug=f"personal-{str(user.id)[:8]}",
            is_personal=True,
            plan=user.plan,
            stripe_customer_id=user.stripe_customer_id,
        )
        db.add(org)
        await db.flush()
        db.add(Membership(organization_id=org.id, user_id=user.id, role="owner"))
        await db.flush()
        logger.info("Auto-created personal_org user=%s org=%s", user.id, org.id)

    return user

CurrentUser = Annotated[Any, Depends(get_current_user)]
