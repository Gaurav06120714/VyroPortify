"""OAuth 2.0 router — app registration, authorize, consent, token exchange.

App management (Clerk-auth)
---------------------------
POST   /api/v1/oauth/apps         Register an app (returns client_secret ONCE)
GET    /api/v1/oauth/apps         List the caller's apps
DELETE /api/v1/oauth/apps/{id}    Delete an app

Authorization flow
------------------
GET    /api/v1/oauth/authorize    Inspect an authorization request (Clerk-auth)
POST   /api/v1/oauth/consent      User approves → returns a one-time code (Clerk-auth)
POST   /api/v1/oauth/token        Public — exchange code+verifier for an access token

Token management (Clerk-auth)
-----------------------------
GET    /api/v1/oauth/grants       List apps that currently hold a token for the user
DELETE /api/v1/oauth/grants/{id}  Revoke a granted token
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, HTTPException, Request, status

from app.core.limiter import limiter
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select

from app.database import DB
from app.models.oauth import (
    OAuthAccessToken,
    OAuthApp,
    OAuthAuthorizationCode,
)
from app.security import CurrentUser
from app.services.oauth import (
    ACCESS_TOKEN_TTL_SECONDS,
    CODE_TTL_SECONDS,
    generate_access_token,
    generate_authorization_code,
    generate_client_id,
    generate_client_secret,
    sha256_hex,
    verify_pkce,
)
from app.routers.api_keys import ALLOWED_SCOPES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth", tags=["OAuth"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateAppRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    redirect_uris: list[HttpUrl] = Field(..., min_length=1)
    homepage_url: HttpUrl | None = None


class CreateAppResponse(BaseModel):
    id: uuid.UUID
    name: str
    client_id: str
    client_secret: str  # only returned once
    redirect_uris: list[str]


class AppResponse(BaseModel):
    id: uuid.UUID
    name: str
    client_id: str
    redirect_uris: list[str]
    homepage_url: str | None
    created_at: datetime


class ConsentRequest(BaseModel):
    client_id: str
    redirect_uri: str
    scopes: list[str]
    code_challenge: str | None = None
    code_challenge_method: str | None = Field(default=None, pattern="^(plain|S256)$")
    state: str | None = None


class ConsentResponse(BaseModel):
    code: str
    state: str | None
    redirect_uri: str


class GrantResponse(BaseModel):
    id: uuid.UUID
    app_id: uuid.UUID
    app_name: str
    scopes: list[str]
    expires_at: datetime
    created_at: datetime


# ── App management ─────────────────────────────────────────────────────────────

@router.post("/apps", response_model=CreateAppResponse, status_code=status.HTTP_201_CREATED)
async def create_app(body: CreateAppRequest, db: DB, current_user: CurrentUser) -> CreateAppResponse:
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    app_row = OAuthApp(
        owner_user_id=current_user.id,
        name=body.name,
        client_id=client_id,
        client_secret_hash=sha256_hex(client_secret),
        redirect_uris=",".join(str(u) for u in body.redirect_uris),
        homepage_url=str(body.homepage_url) if body.homepage_url else None,
    )
    db.add(app_row)
    await db.flush()
    await db.commit()
    await db.refresh(app_row)
    return CreateAppResponse(
        id=app_row.id,
        name=app_row.name,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uris=app_row.redirect_uri_list(),
    )


@router.get("/apps", response_model=list[AppResponse])
async def list_apps(db: DB, current_user: CurrentUser) -> list[AppResponse]:
    result = await db.execute(
        select(OAuthApp).where(OAuthApp.owner_user_id == current_user.id).order_by(OAuthApp.created_at.desc())
    )
    return [
        AppResponse(
            id=a.id,
            name=a.name,
            client_id=a.client_id,
            redirect_uris=a.redirect_uri_list(),
            homepage_url=a.homepage_url,
            created_at=a.created_at,
        )
        for a in result.scalars().all()
    ]


@router.delete("/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(app_id: uuid.UUID, db: DB, current_user: CurrentUser) -> None:
    app_row = await db.get(OAuthApp, app_id)
    if app_row is None or app_row.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    await db.delete(app_row)
    await db.commit()


# ── Authorization flow ─────────────────────────────────────────────────────────

@router.get("/authorize")
async def inspect_authorize(
    client_id: str,
    redirect_uri: str,
    db: DB,
    current_user: CurrentUser,
    scope: str = "",
) -> dict:
    """Frontend hits this with the query params from the third-party app's redirect.

    Returns enough metadata to render a consent screen; doesn't issue anything.
    """
    app_row = (await db.execute(select(OAuthApp).where(OAuthApp.client_id == client_id))).scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown client_id")
    if redirect_uri not in app_row.redirect_uri_list():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri not registered")
    requested = [s for s in scope.split(" ") if s]
    invalid = [s for s in requested if s not in ALLOWED_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scopes: {invalid}. Allowed: {sorted(ALLOWED_SCOPES)}",
        )
    return {
        "app": {
            "id": str(app_row.id),
            "name": app_row.name,
            "homepage_url": app_row.homepage_url,
        },
        "scopes": requested,
        "redirect_uri": redirect_uri,
        "user": {"id": str(current_user.id), "email": current_user.email},
    }


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(body: ConsentRequest, db: DB, current_user: CurrentUser) -> ConsentResponse:
    app_row = (await db.execute(select(OAuthApp).where(OAuthApp.client_id == body.client_id))).scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown client_id")
    if body.redirect_uri not in app_row.redirect_uri_list():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri not registered")
    invalid = [s for s in body.scopes if s not in ALLOWED_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scopes: {invalid}. Allowed: {sorted(ALLOWED_SCOPES)}",
        )

    raw_code = generate_authorization_code()
    code = OAuthAuthorizationCode(
        app_id=app_row.id,
        user_id=current_user.id,
        code_hash=sha256_hex(raw_code),
        redirect_uri=body.redirect_uri,
        scopes=",".join(body.scopes),
        code_challenge=body.code_challenge,
        code_challenge_method=body.code_challenge_method,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=CODE_TTL_SECONDS),
    )
    db.add(code)
    await db.commit()
    return ConsentResponse(code=raw_code, state=body.state, redirect_uri=body.redirect_uri)


# ── Token exchange (public) ────────────────────────────────────────────────────

@router.post("/token")
@limiter.limit("20/minute")   # v3.3.1 — brute-force protection on token exchange
async def token_exchange(
    request: Request,
    db: DB,
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    client_secret: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
) -> dict:
    """RFC 6749 §4.1.3 — authorization_code grant.

    Either client_secret OR code_verifier (PKCE) must be supplied.
    """
    if grant_type != "authorization_code":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_grant_type")

    app_row = (await db.execute(select(OAuthApp).where(OAuthApp.client_id == client_id))).scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")

    row = (
        await db.execute(select(OAuthAuthorizationCode).where(OAuthAuthorizationCode.code_hash == sha256_hex(code)))
    ).scalar_one_or_none()
    if row is None or row.app_id != app_row.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")
    if row.used_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code_already_used")
    if row.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code_expired")
    if row.redirect_uri != redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri_mismatch")

    # Credential check — PKCE if a challenge was set, otherwise the client_secret.
    if row.code_challenge:
        if not code_verifier or not verify_pkce(code_verifier, row.code_challenge, row.code_challenge_method or "S256"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_pkce")
    else:
        if not client_secret or sha256_hex(client_secret) != app_row.client_secret_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")

    raw_token = generate_access_token()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_TTL_SECONDS)
    token = OAuthAccessToken(
        app_id=app_row.id,
        user_id=row.user_id,
        token_hash=sha256_hex(raw_token),
        scopes=row.scopes,
        expires_at=expires_at,
    )
    row.used_at = datetime.now(timezone.utc)
    db.add(token)
    await db.commit()

    return {
        "access_token": raw_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
        "scope": row.scopes.replace(",", " "),
    }


# ── Grant management (user-facing) ─────────────────────────────────────────────

@router.get("/grants", response_model=list[GrantResponse])
async def list_grants(db: DB, current_user: CurrentUser) -> list[GrantResponse]:
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(OAuthAccessToken, OAuthApp)
            .join(OAuthApp, OAuthApp.id == OAuthAccessToken.app_id)
            .where(
                OAuthAccessToken.user_id == current_user.id,
                OAuthAccessToken.revoked_at.is_(None),
                OAuthAccessToken.expires_at > now,
            )
            .order_by(OAuthAccessToken.created_at.desc())
        )
    ).all()
    return [
        GrantResponse(
            id=t.id,
            app_id=a.id,
            app_name=a.name,
            scopes=t.scope_list(),
            expires_at=t.expires_at,
            created_at=t.created_at,
        )
        for (t, a) in rows
    ]


@router.delete("/grants/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grant(token_id: uuid.UUID, db: DB, current_user: CurrentUser) -> None:
    tok = await db.get(OAuthAccessToken, token_id)
    if tok is None or tok.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    if tok.revoked_at is None:
        tok.revoked_at = datetime.now(timezone.utc)
        await db.commit()
