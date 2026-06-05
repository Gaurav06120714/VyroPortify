"""OAuth 2.0 helpers: client/token generation, PKCE verification (v3.0.2)."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.oauth import OAuthAccessToken
from app.models.user import User

CLIENT_ID_PREFIX = "vpcli_"
CLIENT_SECRET_PREFIX = "vpsec_"
ACCESS_TOKEN_PREFIX = "oat_"
AUTH_CODE_PREFIX = "oac_"

CODE_TTL_SECONDS = 600         # 10 minutes
ACCESS_TOKEN_TTL_SECONDS = 3600 * 24 * 30  # 30 days


def generate_client_id() -> str:
    return CLIENT_ID_PREFIX + secrets.token_urlsafe(16)[:24]


def generate_client_secret() -> str:
    return CLIENT_SECRET_PREFIX + secrets.token_urlsafe(32)[:40]


def generate_authorization_code() -> str:
    return AUTH_CODE_PREFIX + secrets.token_urlsafe(32)[:40]


def generate_access_token() -> str:
    return ACCESS_TOKEN_PREFIX + secrets.token_urlsafe(32)[:40]


def sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_pkce(verifier: str, challenge: str, method: str) -> bool:
    """RFC 7636: S256 = base64url(SHA256(verifier)); plain = verifier itself."""
    if method == "plain":
        return hmac.compare_digest(verifier, challenge)
    if method == "S256":
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return hmac.compare_digest(expected, challenge)
    return False


class OAuthTokenAuth:
    """Resolved OAuth bearer-token context — the user plus the granted scopes."""

    def __init__(self, user: User, token: OAuthAccessToken):
        self.user = user
        self.token = token
        self.scopes = token.scope_list()

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"OAuth token missing required scope: {scope}",
            )


async def get_oauth_token_auth(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> OAuthTokenAuth:
    """FastAPI dependency: validate a `Authorization: Bearer oat_…` token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raw = authorization.split(" ", 1)[1].strip()
    if not raw.startswith(ACCESS_TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
        )

    result = await db.execute(
        select(OAuthAccessToken).where(OAuthAccessToken.token_hash == sha256_hex(raw))
    )
    tok = result.scalar_one_or_none()
    if tok is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not tok.is_active(datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or expired"
        )

    user = await db.get(User, tok.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner missing")
    return OAuthTokenAuth(user=user, token=tok)
