"""Public REST API — authenticated by personal API key (v3.0.0).

All endpoints under `/api/v1/public` require an `Authorization: Bearer vp_…`
header and enforce the scope listed on each route.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.database import DB
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.services.api_keys import APIKeyAuth, require_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public API"])


class PortfolioOut(BaseModel):
    id: uuid.UUID
    slug: str
    status: str
    template_id: str | None
    is_public: bool
    views: int
    html_url: str | None
    custom_domain: str | None


class ResumeOut(BaseModel):
    id: uuid.UUID
    status: str
    original_filename: str | None
    file_type: str | None


@router.get("/me")
async def whoami(auth: APIKeyAuth = Depends(require_scope("portfolios:read"))) -> dict:
    return {
        "user_id": str(auth.user.id),
        "email": auth.user.email,
        "plan": auth.user.plan,
        "scopes": auth.scopes,
        "key_prefix": auth.key.prefix,
    }


@router.get("/portfolios", response_model=list[PortfolioOut])
async def list_portfolios(
    db: DB,
    auth: APIKeyAuth = Depends(require_scope("portfolios:read")),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[PortfolioOut]:
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == auth.user.id)
        .order_by(Portfolio.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_portfolio_out(p) for p in result.scalars().all()]


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioOut)
async def get_portfolio(
    portfolio_id: uuid.UUID,
    db: DB,
    auth: APIKeyAuth = Depends(require_scope("portfolios:read")),
) -> PortfolioOut:
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == auth.user.id
        )
    )
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return _portfolio_out(p)


@router.get("/resumes", response_model=list[ResumeOut])
async def list_resumes(
    db: DB,
    auth: APIKeyAuth = Depends(require_scope("resumes:read")),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ResumeOut]:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == auth.user.id)
        .order_by(Resume.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        ResumeOut(
            id=r.id,
            status=r.status,
            original_filename=r.original_filename,
            file_type=r.file_type,
        )
        for r in result.scalars().all()
    ]


def _portfolio_out(p: Portfolio) -> PortfolioOut:
    return PortfolioOut(
        id=p.id,
        slug=p.slug,
        status=p.status,
        template_id=p.template_id,
        is_public=p.is_public,
        views=p.views,
        html_url=p.html_url,
        custom_domain=p.custom_domain,
    )
