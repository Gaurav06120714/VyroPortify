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

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select

from app.core.authz import assert_owner, require_plan
from app.core.cache import PORTFOLIO_PAGE_TTL, cache
from app.core.enums import Plan, PortfolioStatus, TemplateID
from app.core.exceptions import PlanLimitExceeded
from app.core.limiter import limiter
from app.database import DB
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.models.user import User
from app.schemas.portfolio import (
    CustomDomainRequest,
    CustomDomainResponse,
    GeneratePortfolioRequest,
    GeneratePortfolioResponse,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioStatusResponse,
)
from app.security import CurrentUser
from app.services import domain_verification

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
    portfolio_id: uuid.UUID,
    user: User,
    db: DB,
    *,
    min_role: str = "viewer",
) -> Portfolio:
    # B4: ownership OR org membership. min_role lets mutating routes
    # require "editor" while read paths accept "viewer". Default keeps
    # current behavior backwards-compatible for read endpoints.
    from app.core.authz import assert_resource_access

    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id)
    )
    return await assert_resource_access(
        db, result.scalar_one_or_none(), user, min_role=min_role,
    )


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
    limit: int = 20,
    offset: int = 0,
) -> PortfolioListResponse:
    # Offset pagination (v1.2.4). Cap limit so a malicious client can't
    # request 100k rows and OOM the server. Total is returned so the FE
    # can render "x of N" without a second roundtrip.
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    total_res = await db.execute(
        select(func.count()).select_from(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    total = total_res.scalar_one()

    rows = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.created_at.desc())
        .limit(limit)
        .offset(offset)
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
@limiter.limit("120/minute")
async def get_public_portfolio(request: Request, slug: str, db: DB) -> PortfolioResponse:
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

    # Increment view counter (best-effort, async) + insert a PortfolioView
    # row for per-visitor analytics. Session token is SHA-256(ip + UA + day)
    # so the same visitor on the same day collapses, no PII stored.
    #
    # B16 fix: increment via UPDATE … SET views = views + 1 instead of
    # read-modify-write on the ORM instance. Two concurrent requests
    # would both read N, both write N+1 → undercount by 1 per race.
    # Atomic SQL increment is collision-free.
    try:
        import hashlib
        from datetime import date

        from sqlalchemy import update

        from app.models.portfolio_view import PortfolioView

        await db.execute(
            update(Portfolio)
            .where(Portfolio.id == p.id)
            .values(views=Portfolio.views + 1)
        )

        client_ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")
        token = hashlib.sha256(
            f"{client_ip}|{ua}|{date.today().isoformat()}".encode()
        ).hexdigest()
        referrer = (request.headers.get("referer") or "")[:255] or None
        # CF-IPCountry / Vercel-IP-Country provide ISO-2 country codes for free.
        country = (
            request.headers.get("cf-ipcountry")
            or request.headers.get("x-vercel-ip-country")
        )
        country = country[:2].upper() if country else None
        db.add(
            PortfolioView(
                portfolio_id=p.id,
                session_token=token,
                referrer=referrer,
                country=country,
            )
        )
        await db.commit()
    except Exception:
        # Analytics failures must never 500 a public page view.
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
    p = await _get_portfolio_or_404(portfolio_id, current_user, db, min_role="editor")
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
    p = await _get_portfolio_or_404(portfolio_id, current_user, db, min_role="editor")
    # Invalidate public cache before deletion
    if p.slug:
        await cache.delete(f"portfolio:public:{p.slug}")
    await db.delete(p)
    logger.info("Portfolio deleted id=%s user=%s", portfolio_id, current_user.id)


# ── Analytics (v2.0.3) ─────────────────────────────────────────────────────────

@router.get(
    "/{portfolio_id}/analytics",
    summary="Per-portfolio analytics summary (owner-only)",
)
async def portfolio_analytics(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    days: int = 30,
) -> dict:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db, min_role="editor")

    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func as sql_func

    from app.models.portfolio_view import PortfolioView

    days = max(1, min(days, 365))
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total + unique visitors in the window.
    totals_q = await db.execute(
        select(
            sql_func.count(PortfolioView.id).label("total"),
            sql_func.count(sql_func.distinct(PortfolioView.session_token)).label("unique"),
        ).where(
            PortfolioView.portfolio_id == p.id,
            PortfolioView.created_at >= since,
        )
    )
    totals = totals_q.one()

    # Per-day buckets — server-formatted as ISO date strings for the
    # frontend to drop straight into a chart.
    by_day_q = await db.execute(
        select(
            sql_func.date_trunc("day", PortfolioView.created_at).label("day"),
            sql_func.count(PortfolioView.id),
        )
        .where(
            PortfolioView.portfolio_id == p.id,
            PortfolioView.created_at >= since,
        )
        .group_by("day")
        .order_by("day")
    )
    by_day = [
        {"day": d.isoformat() if d else None, "views": int(c)}
        for d, c in by_day_q.all()
    ]

    # Top referrers + top countries (capped).
    referrers_q = await db.execute(
        select(
            PortfolioView.referrer,
            sql_func.count(PortfolioView.id),
        )
        .where(
            PortfolioView.portfolio_id == p.id,
            PortfolioView.created_at >= since,
            PortfolioView.referrer.isnot(None),
        )
        .group_by(PortfolioView.referrer)
        .order_by(sql_func.count(PortfolioView.id).desc())
        .limit(10)
    )
    referrers = [
        {"referrer": r, "views": int(c)} for r, c in referrers_q.all()
    ]

    countries_q = await db.execute(
        select(
            PortfolioView.country,
            sql_func.count(PortfolioView.id),
        )
        .where(
            PortfolioView.portfolio_id == p.id,
            PortfolioView.created_at >= since,
            PortfolioView.country.isnot(None),
        )
        .group_by(PortfolioView.country)
        .order_by(sql_func.count(PortfolioView.id).desc())
        .limit(10)
    )
    countries = [
        {"country": c, "views": int(n)} for c, n in countries_q.all()
    ]

    return {
        "portfolio_id": str(p.id),
        "window_days": days,
        "total_views": int(totals.total or 0),
        "unique_visitors": int(totals.unique or 0),
        "lifetime_views": int(p.views or 0),
        "by_day": by_day,
        "referrers": referrers,
        "countries": countries,
    }


# ── Custom domain (Pro) ────────────────────────────────────────────────────────
# Three endpoints back the custom-domain feature:
#   PUT    /{id}/custom-domain   attach a domain (validate + store, Pro-only)
#   GET    /{id}/custom-domain   poll DNS verification status
#   DELETE /{id}/custom-domain   detach
#
# We don't persist a `verified` flag yet. CNAME state can change at any time,
# so the source of truth is always a live DNS lookup. The endpoint is cheap
# (one CNAME query, sub-50ms) and frontends will poll it during setup only.


def _domain_response(p: Portfolio, result: domain_verification.VerificationResult | None) -> CustomDomainResponse:
    if result is None:
        return CustomDomainResponse(
            portfolio_id=p.id,
            domain=None,
            verified=False,
            cname_target=None,
            expected_target=domain_verification.CUSTOM_DOMAIN_TARGET,
            detail="No custom domain attached",
        )
    return CustomDomainResponse(
        portfolio_id=p.id,
        domain=result.domain,
        verified=result.verified,
        cname_target=result.cname_target,
        expected_target=result.expected_target,
        detail=result.detail,
    )


@router.put(
    "/{portfolio_id}/custom-domain",
    response_model=CustomDomainResponse,
    summary="Attach a custom domain to a portfolio (Pro only)",
    dependencies=[Depends(require_plan(Plan.PRO, feature="Custom domain"))],
)
async def attach_custom_domain(
    portfolio_id: uuid.UUID,
    body: CustomDomainRequest,
    current_user: CurrentUser,
    db: DB,
) -> CustomDomainResponse:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db, min_role="editor")

    try:
        domain = domain_verification.normalize_domain(body.domain)
    except domain_verification.DomainValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Uniqueness check: the case-insensitive partial unique index in the DB is
    # the source of truth, but a pre-check gives a clean 409 instead of a
    # generic 500 on IntegrityError.
    existing = await db.execute(
        select(Portfolio).where(
            func.lower(Portfolio.custom_domain) == domain,
            Portfolio.id != portfolio_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Domain already in use")

    p.custom_domain = domain
    await db.commit()
    await cache.delete(f"portfolio:public:{p.slug}")

    # Run DNS lookup off the event loop — dnspython is blocking.
    result = await anyio.to_thread.run_sync(domain_verification.verify_cname, domain)
    logger.info(
        "custom_domain_attached portfolio=%s domain=%s verified=%s",
        portfolio_id, domain, result.verified,
    )
    return _domain_response(p, result)


@router.get(
    "/{portfolio_id}/custom-domain",
    response_model=CustomDomainResponse,
    summary="Get custom-domain status (live CNAME check)",
)
async def get_custom_domain(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> CustomDomainResponse:
    # Read endpoint — viewer role is enough.
    p = await _get_portfolio_or_404(portfolio_id, current_user, db)
    if not p.custom_domain:
        return _domain_response(p, None)

    result = await anyio.to_thread.run_sync(
        domain_verification.verify_cname, p.custom_domain
    )
    return _domain_response(p, result)


@router.delete(
    "/{portfolio_id}/custom-domain",
    response_model=CustomDomainResponse,
    summary="Detach the custom domain from a portfolio",
)
async def detach_custom_domain(
    portfolio_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> CustomDomainResponse:
    p = await _get_portfolio_or_404(portfolio_id, current_user, db, min_role="editor")
    p.custom_domain = None
    await db.commit()
    await cache.delete(f"portfolio:public:{p.slug}")
    logger.info("custom_domain_detached portfolio=%s user=%s", portfolio_id, current_user.id)
    return _domain_response(p, None)
