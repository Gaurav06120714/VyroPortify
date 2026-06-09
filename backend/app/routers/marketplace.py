"""Template marketplace router (v2.1).

v2.1.0 endpoints
----------------
GET    /api/v1/marketplace/templates                  Public listing (filter: status=approved, category, q, sort)
GET    /api/v1/marketplace/templates/{id}             Detail
POST   /api/v1/marketplace/templates                  Submit (caller becomes author, status=pending)
POST   /api/v1/marketplace/templates/{id}/moderate    Moderator-only: approve / reject

v2.1.1 (paid templates) is in routers/connect.py (Stripe Connect).
v2.1.2 reviews are below.

Moderation auth
---------------
For the v2.1 MVP, "moderator" = any user whose primary org has the
``is_personal=false`` and the user is owner. That gates moderation
to deliberate, team-account users without introducing a global admin
role (which arrives in v3.0). Trivially extended later by swapping
the dependency in `_require_moderator`.
"""

import logging
import re
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import DB
from app.models.organization import Membership, Organization
from app.models.template import Template, TemplateReview
from app.models.user import User
from app.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

class TemplateSubmit(BaseModel):
    id: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=100)
    preview_url: str | None = Field(default=None, max_length=2048)
    price_cents: int = Field(default=0, ge=0, le=100_000)
    config: dict | None = None

class ModerateAction(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    reason: str | None = Field(default=None, max_length=400)

class TemplateOut(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    category: str | None
    preview_url: str | None
    is_pro: bool
    price_cents: int
    status: str
    author_user_id: uuid.UUID | None
    downloads_count: int
    rating_average: float
    rating_count: int

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: str
    user_id: uuid.UUID
    rating: int
    comment: str | None

async def _require_moderator(current_user: CurrentUser, db: DB) -> User:
    """Owner of any non-personal org. See module docstring for the rationale."""
    result = await db.execute(
        select(Membership)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(
            Membership.user_id == current_user.id,
            Membership.role == "owner",
            Organization.is_personal.is_(False),
        )
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required",
        )
    return current_user

@router.get(
    "/templates",
    response_model=list[TemplateOut],
    summary="List marketplace templates",
)
async def list_templates(
    db: DB,
    status_filter: str = "approved",
    category: str | None = None,
    q: str | None = None,
    sort: str = "popular",
    limit: int = 24,
    offset: int = 0,
) -> list[TemplateOut]:
    """Public listing.

    Default filter is `status=approved` so unapproved submissions never leak.
    `q` does a case-insensitive partial match on name and description.
    `sort` ∈ popular | newest | rating | price_low | price_high.
    """
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    stmt = select(Template).where(Template.status == status_filter)
    if category:
        stmt = stmt.where(Template.category == category)
    if q:
        needle = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Template.name).like(needle),
                func.lower(func.coalesce(Template.description, "")).like(needle),
            )
        )

    if sort == "newest":
        stmt = stmt.order_by(desc(Template.created_at))
    elif sort == "rating":
        stmt = stmt.order_by(desc(Template.rating_average), desc(Template.rating_count))
    elif sort == "price_low":
        stmt = stmt.order_by(Template.price_cents.asc())
    elif sort == "price_high":
        stmt = stmt.order_by(Template.price_cents.desc())
    else:  
        stmt = stmt.order_by(desc(Template.downloads_count), desc(Template.rating_average))

    stmt = stmt.limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return [TemplateOut.model_validate(t) for t in rows]

@router.get(
    "/templates/{template_id}",
    response_model=TemplateOut,
    summary="Get one template",
)
async def get_template(template_id: str, db: DB) -> TemplateOut:
    t = await db.get(Template, template_id)
    if t is None or t.status not in ("approved", "pending"):
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateOut.model_validate(t)

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")

@router.post(
    "/templates",
    response_model=TemplateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a community template (status=pending)",
)
async def submit_template(
    body: TemplateSubmit, current_user: CurrentUser, db: DB
) -> TemplateOut:
    if not _SLUG_RE.match(body.id):
        raise HTTPException(status_code=400, detail="Template id must be lowercase a-z, 0-9, hyphens only")

    from sqlalchemy.exc import IntegrityError

    existing = await db.get(Template, body.id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Template id already exists")

    t = Template(
        id=body.id,
        name=body.name,
        description=body.description,
        category=body.category,
        preview_url=body.preview_url,
        is_pro=False,
        price_cents=body.price_cents,
        config=body.config,
        author_user_id=current_user.id,
        status="pending",
    )
    db.add(t)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Template id already exists"
        )
    await db.refresh(t)
    logger.info("template_submitted id=%s author=%s", t.id, current_user.id)
    return TemplateOut.model_validate(t)

@router.post(
    "/templates/{template_id}/moderate",
    response_model=TemplateOut,
    summary="Approve or reject a pending template (moderator only)",
)
async def moderate_template(
    template_id: str,
    body: ModerateAction,
    current_user: CurrentUser,
    db: DB,
    _moderator: User = Depends(_require_moderator),
) -> TemplateOut:
    t = await db.get(Template, template_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if t.status != "pending":
        raise HTTPException(status_code=400, detail=f"Template is {t.status}, not pending")

    t.status = "approved" if body.action == "approve" else "rejected"
    await db.commit()
    logger.info(
        "template_%s id=%s moderator=%s reason=%r",
        t.status, t.id, current_user.id, body.reason,
    )
    return TemplateOut.model_validate(t)

@router.get(
    "/templates/{template_id}/reviews",
    response_model=list[ReviewOut],
    summary="List reviews for a template",
)
async def list_reviews(
    template_id: str, db: DB, limit: int = 20, offset: int = 0
) -> list[ReviewOut]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    rows = (
        await db.execute(
            select(TemplateReview)
            .where(TemplateReview.template_id == template_id)
            .order_by(desc(TemplateReview.created_at))
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return [ReviewOut.model_validate(r) for r in rows]

@router.post(
    "/templates/{template_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add or replace your review for a template",
)
async def add_review(
    template_id: str,
    body: ReviewIn,
    current_user: CurrentUser,
    db: DB,
) -> ReviewOut:
    
    tpl = await db.get(Template, template_id)
    if tpl is None or tpl.status != "approved":
        raise HTTPException(status_code=404, detail="Template not found")

    if tpl.author_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't review your own template")

    stmt = (
        pg_insert(TemplateReview)
        .values(
            template_id=template_id,
            user_id=current_user.id,
            rating=body.rating,
            comment=body.comment,
        )
        .on_conflict_do_update(
            constraint="uq_template_reviews_template_user",
            set_={"rating": body.rating, "comment": body.comment},
        )
        .returning(TemplateReview)
    )
    result = await db.execute(stmt)
    review = result.scalar_one()

    agg = await db.execute(
        select(
            func.coalesce(func.avg(TemplateReview.rating), 0).label("avg"),
            func.count(TemplateReview.id).label("count"),
        ).where(TemplateReview.template_id == template_id)
    )
    row = agg.one()
    tpl.rating_average = Decimal(row.avg).quantize(Decimal("0.01"))
    tpl.rating_count = int(row.count)
    await db.commit()
    await db.refresh(review)
    return ReviewOut.model_validate(review)
