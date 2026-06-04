"""Portfolio router.

Endpoints
---------
POST  /api/v1/portfolio/generate        Trigger portfolio generation (async)
GET   /api/v1/portfolio/{id}/status     Poll generation status
GET   /api/v1/portfolio/                List current user's portfolios
GET   /api/v1/portfolio/p/{slug}        Public portfolio by slug (no auth)
PUT   /api/v1/portfolio/{id}/publish    Toggle publish status
DELETE /api/v1/portfolio/{id}           Delete portfolio
"""

import logging
import re
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.core.authz import assert_owner
from app.core.cache import PORTFOLIO_PAGE_TTL, cache
from app.core.enums import Plan, PortfolioStatus, TemplateID
from app.core.exceptions import PlanLimitExceeded
from app.core.limiter import limiter
from app.database import DB
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.models.user import User
from app.schemas.portfolio import (
    GeneratePortfolioRequest,
    GeneratePortfolioResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioStatusResponse,
)
from app.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slugify(name: str, user_id: uuid.UUID) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = slug[:40]
    return f"{slug}-{str(user_id)[:8]}"


async def _get_portfolio_or_404(
    portfolio_id: uuid.UUID, user: User, db: DB
) -> Portfolio:
    # Fetch by primary key only; ownership is enforced by assert_owner so the
    # policy lives in a single audited place (app.core.authz).
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id)
    )
    return assert_owner(result.scalar_one_or_none(), user)


def _to_response(p: Portfolio) -> PortfolioResponse:
    return PortfolioResponse(
        id=p.id,
        user_id=p.user_id,
        resume_id=p.resume_id,
        slug=p.slug,
        template_id=p.template_id,
        content=p.content,
        html_url=p.html_url,
        is_public=p.is_public,
        views=p.views,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ── POST /generate ─────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GeneratePortfolioResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger async portfolio generation from a parsed resume",
)
@limiter.limit("10/minute")
async def generate_portfolio(
    request: Request,
    body: GeneratePortfolioRequest,
    current_user: CurrentUser,
    db: DB,
) -> GeneratePortfolioResponse:
    # ── Free-tier enforcement ──────────────────────────────────────────────────
    FREE_PORTFOLIO_LIMIT = 3
    FREE_TEMPLATES = {TemplateID.AURORA}  # free users may only use the aurora template

    if current_user.plan == Plan.FREE:
        count = await db.scalar(
            select(func.count())
            .select_from(Portfolio)
            .where(Portfolio.user_id == current_user.id)
        )
        if (count or 0) >= FREE_PORTFOLIO_LIMIT:
            raise PlanLimitExceeded(
                f"Free plan allows {FREE_PORTFOLIO_LIMIT} portfolios. "
                "Upgrade to Pro for unlimited portfolios."
            )

        requested_template = TemplateID(body.template_id) if body.template_id else TemplateID.AURORA
        if requested_template not in FREE_TEMPLATES:
            raise PlanLimitExceeded(
                f"Template '{body.template_id}' requires a Pro plan. "
                "Upgrade to access all templates."
            )

    # Verify resume belongs to user and is parsed
    result = await db.execute(
        select(Resume).where(
            Resume.id == body.resume_id, Resume.user_id == current_user.id
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.status != "done" or not resume.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume parsing is not complete yet. Poll /resume/{id}/status first.",
        )

    # Build slug from parsed name
    name = resume.parsed_data.get("full_name", str(current_user.id))
    slug = _slugify(name, current_user.id)

    # Create portfolio record
    portfolio = Portfolio(
        user_id=current_user.id,
        resume_id=body.resume_id,
        slug=slug,
        template_id=body.template_id,
        status=PortfolioStatus.QUEUED,
    )
    db.add(portfolio)
    await db.flush()

    # Enqueue Celery task
    job_queued = False
    try:
        from app.workers.tasks.generate_portfolio import generate_portfolio_task
        generate_portfolio_task.delay(str(portfolio.id))
        job_queued = True
        logger.info("Queued generate_portfolio_task for portfolio %s", portfolio.id)
    except Exception as exc:
        logger.error("Failed to enqueue generation task: %s", exc)

    return GeneratePortfolioResponse(
        portfolio_id=portfolio.id,
        job_queued=job_queued,
        message="Portfolio generation started. Poll /portfolio/{id}/status for updates.",
    )


# ── GET /{id}/status ───────────────────────────────────────────────────────────

@router.get(
    "/{portfolio_id}/status",
    response_model=PortfolioStatusResponse,
    summary="Poll portfolio generation status",
)
async def get_portfolio_status(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> PortfolioStatusResponse:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db)
    ai_fallback = p.content.get("_ai_failed", False) if p.content else False
    return PortfolioStatusResponse(
        id=p.id, status=p.status, html_url=p.html_url, slug=p.slug, ai_fallback=ai_fallback
    )


# ── GET / (list) ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PortfolioListResponse,
    summary="List all portfolios for the current user",
)
async def list_portfolios(
    current_user: CurrentUser,
    db: DB,
) -> PortfolioListResponse:
    total_res = await db.execute(
        select(func.count()).select_from(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    total = total_res.scalar_one()

    rows = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.created_at.desc())
    )
    portfolios = rows.scalars().all()
    return PortfolioListResponse(items=[_to_response(p) for p in portfolios], total=total)


# ── GET /sitemap — public slugs for sitemap.xml ───────────────────────────────

@router.get(
    "/sitemap",
    summary="Return public portfolio slugs for sitemap generation (no auth)",
)
async def portfolio_sitemap(db: DB) -> list[dict]:
    from app.core.cache import TEMPLATE_LIST_TTL

    cache_key = "portfolio:sitemap"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    rows = await db.execute(
        select(Portfolio.slug, Portfolio.updated_at)
        .where(Portfolio.is_public.is_(True), Portfolio.status == "published")  # noqa: E501
        .order_by(Portfolio.updated_at.desc())
        .limit(5000)
    )
    items = [{"slug": row.slug, "updated_at": row.updated_at.isoformat()} for row in rows]
    await cache.set(cache_key, items, ttl=TEMPLATE_LIST_TTL)
    return items


# ── GET /p/{slug} — PUBLIC ─────────────────────────────────────────────────────

@router.get(
    "/p/{slug}",
    response_model=PortfolioResponse,
    summary="Get a public portfolio by slug (no auth required)",
)
async def get_public_portfolio(slug: str, db: DB) -> PortfolioResponse:
    cache_key = f"portfolio:public:{slug}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        logger.debug("Cache HIT portfolio slug=%s", slug)
        return PortfolioResponse(**cached)

    result = await db.execute(
        select(Portfolio).where(Portfolio.slug == slug, Portfolio.is_public.is_(True))
    )
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    # Increment view counter (best-effort, async)
    try:
        p.views = (p.views or 0) + 1
        await db.commit()
    except Exception:
        pass

    response = _to_response(p)

    # Cache for 1 hour
    await cache.set(cache_key, response.model_dump(), ttl=PORTFOLIO_PAGE_TTL)

    return response


# ── PUT /{id}/publish ──────────────────────────────────────────────────────────

@router.put(
    "/{portfolio_id}/publish",
    response_model=PortfolioResponse,
    summary="Toggle portfolio publish status",
)
async def toggle_publish(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> PortfolioResponse:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db)
    p.is_public = not p.is_public
    await db.commit()
    # Invalidate public cache
    if p.slug:
        await cache.delete(f"portfolio:public:{p.slug}")
    return _to_response(p)


# ── DELETE /{id} ───────────────────────────────────────────────────────────────

@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a portfolio",
)
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db)
    # Invalidate public cache before deletion
    if p.slug:
        await cache.delete(f"portfolio:public:{p.slug}")
    await db.delete(p)
    logger.info("Portfolio deleted id=%s user=%s", portfolio_id, current_user.id)
