"""API key management — Clerk-authenticated.

Endpoints
---------
POST   /api/v1/keys           Issue a new key (returns raw key ONCE)
GET    /api/v1/keys           List the caller's keys (metadata only)
DELETE /api/v1/keys/{key_id}  Revoke a key
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database import DB
from app.models.api_key import APIKey
from app.security import CurrentUser
from app.services.api_keys import (
    display_prefix,
    generate_raw_key,
    hash_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keys", tags=["API Keys"])

ALLOWED_SCOPES = {
    "portfolios:read",
    "portfolios:write",
    "resumes:read",
    "resumes:write",
}

class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None

class CreateKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime
    key: str  

class KeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

@router.post("", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(body: CreateKeyRequest, db: DB, current_user: CurrentUser) -> CreateKeyResponse:
    invalid = [s for s in body.scopes if s not in ALLOWED_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scopes: {invalid}. Allowed: {sorted(ALLOWED_SCOPES)}",
        )

    raw = generate_raw_key()
    key = APIKey(
        user_id=current_user.id,
        name=body.name,
        prefix=display_prefix(raw),
        key_hash=hash_key(raw),
        scopes=",".join(body.scopes),
        expires_at=body.expires_at,
    )
    db.add(key)
    await db.flush()
    await db.commit()
    await db.refresh(key)
    logger.info("api_key.created user=%s key=%s", current_user.id, key.id)

    return CreateKeyResponse(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        scopes=key.scope_list(),
        expires_at=key.expires_at,
        created_at=key.created_at,
        key=raw,
    )

@router.get("", response_model=list[KeyResponse])
async def list_keys(db: DB, current_user: CurrentUser) -> list[KeyResponse]:
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        KeyResponse(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            scopes=k.scope_list(),
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            revoked_at=k.revoked_at,
            created_at=k.created_at,
        )
        for k in keys
    ]

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(key_id: uuid.UUID, db: DB, current_user: CurrentUser) -> None:
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    if key.revoked_at is None:
        key.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("api_key.revoked user=%s key=%s", current_user.id, key.id)
