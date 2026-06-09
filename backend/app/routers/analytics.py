"""Org-scoped analytics API (v3.1.0).

GET /api/v1/analytics/orgs/{org_id}/overview   Headline stats for the org
GET /api/v1/analytics/orgs/{org_id}/timeseries Daily portfolio creation + views
GET /api/v1/analytics/orgs/{org_id}/top        Top portfolios by views

All endpoints require admin+ membership on the org.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.authz import require_role
from app.database import DB
from app.models.audit_event import AuditEvent
from app.security import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

class OverviewResponse(BaseModel):
    org_id: uuid.UUID
    total_portfolios: int
    published_portfolios: int
    total_views: int
    total_resumes: int
    members: int
    audit_events_last_30d: int

class TimePoint(BaseModel):
    day: datetime
    portfolios_created: int
    views: int

class TopPortfolio(BaseModel):
    id: uuid.UUID
    slug: str
    views: int

@router.get(
    "/orgs/{org_id}/overview",
    response_model=OverviewResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def overview(org_id: uuid.UUID, db: DB, current_user: CurrentUser) -> OverviewResponse:
    from app.models.organization import Membership
    from app.models.portfolio import Portfolio
    from app.models.resume import Resume

    total_portfolios = await db.scalar(
        select(func.count(Portfolio.id)).where(Portfolio.organization_id == org_id)
    ) or 0
    published_portfolios = await db.scalar(
        select(func.count(Portfolio.id)).where(
            Portfolio.organization_id == org_id, Portfolio.status == "published"
        )
    ) or 0
    total_views = await db.scalar(
        select(func.coalesce(func.sum(Portfolio.views), 0)).where(Portfolio.organization_id == org_id)
    ) or 0
    total_resumes = await db.scalar(
        select(func.count(Resume.id)).where(Resume.organization_id == org_id)
    ) or 0
    members = await db.scalar(
        select(func.count(Membership.id)).where(Membership.organization_id == org_id)
    ) or 0
    since = datetime.now(timezone.utc) - timedelta(days=30)
    audit_30d = await db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.organization_id == org_id, AuditEvent.created_at >= since
        )
    ) or 0

    return OverviewResponse(
        org_id=org_id,
        total_portfolios=int(total_portfolios),
        published_portfolios=int(published_portfolios),
        total_views=int(total_views),
        total_resumes=int(total_resumes),
        members=int(members),
        audit_events_last_30d=int(audit_30d),
    )

@router.get(
    "/orgs/{org_id}/timeseries",
    response_model=list[TimePoint],
    dependencies=[Depends(require_role("admin"))],
)
async def timeseries(
    org_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=180),
) -> list[TimePoint]:
    from app.models.portfolio import Portfolio

    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_col = func.date_trunc("day", Portfolio.created_at).label("day")
    rows = (
        await db.execute(
            select(
                day_col,
                func.count(Portfolio.id).label("created"),
                func.coalesce(func.sum(Portfolio.views), 0).label("views"),
            )
            .where(Portfolio.organization_id == org_id, Portfolio.created_at >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
    ).all()
    return [TimePoint(day=r.day, portfolios_created=int(r.created), views=int(r.views)) for r in rows]

@router.get(
    "/orgs/{org_id}/top",
    response_model=list[TopPortfolio],
    dependencies=[Depends(require_role("admin"))],
)
async def top(
    org_id: uuid.UUID, db: DB, current_user: CurrentUser, limit: int = Query(default=10, ge=1, le=50)
) -> list[TopPortfolio]:
    from app.models.portfolio import Portfolio

    rows = (
        await db.execute(
            select(Portfolio.id, Portfolio.slug, Portfolio.views)
            .where(Portfolio.organization_id == org_id, Portfolio.status == "published")
            .order_by(Portfolio.views.desc())
            .limit(limit)
        )
    ).all()
    return [TopPortfolio(id=r.id, slug=r.slug, views=int(r.views)) for r in rows]
