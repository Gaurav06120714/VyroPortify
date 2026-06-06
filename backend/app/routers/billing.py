"""Billing router — Stripe checkout, portal, and webhook.

Endpoints
---------
POST   /api/v1/billing/create-checkout   Create Stripe checkout session → return URL
POST   /api/v1/billing/webhook           Stripe webhook (no auth — verified by sig)
GET    /api/v1/billing/portal            Return portal session URL for subscription mgmt
GET    /api/v1/billing/status            Current user's plan + subscription details
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

import anyio
import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.core.enums import Plan
from app.core.limiter import limiter, log_security_event
from app.core.rate_limit import RateLimitCheck
from app.database import DB
from app.models.user import User
from app.security import CurrentUser
from app.services import stripe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class PortalResponse(BaseModel):
    portal_url: str

class BillingStatusResponse(BaseModel):
    plan: str
    stripe_customer_id: str | None
    subscription_status: str | None
    current_period_end: int | None        # unix timestamp
    cancel_at_period_end: bool | None


# ── POST /create-checkout ──────────────────────────────────────────────────────

@router.post(
    "/create-checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Stripe Checkout session for Pro plan ($9/mo)",
    dependencies=[
        # 5 checkout attempts / hour / IP — prevents session flooding
        Depends(RateLimitCheck("billing:checkout", max_per_ip=5, window_seconds=3600)),
    ],
)
async def create_checkout(current_user: CurrentUser, db: DB, request: Request) -> CheckoutResponse:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    if current_user.plan == Plan.PRO:
        raise HTTPException(status_code=400, detail="You're already on the Pro plan")

    # Ensure the user has a Stripe customer record
    if not current_user.stripe_customer_id:
        cid = await anyio.to_thread.run_sync(
            lambda: stripe_service.get_or_create_customer(
                user_id=str(current_user.id),
                email=current_user.email,
                name=current_user.name,
            )
        )
        current_user.stripe_customer_id = cid
        await db.flush()

    # v2.0.4 — per-seat checkout. Resolve the caller's primary org and
    # pass seat count = active membership count. For personal orgs that's
    # always 1, so the checkout behaves exactly like v1; for team orgs
    # we bill seats * unit price.
    from sqlalchemy import func as sql_func

    from app.models.organization import Membership

    org_id: str | None = None
    seats = 1
    member_row = await db.execute(
        select(Membership).where(Membership.user_id == current_user.id).limit(1)
    )
    membership = member_row.scalar_one_or_none()
    if membership is not None:
        org_id = str(membership.organization_id)
        seat_count = await db.scalar(
            select(sql_func.count(Membership.id)).where(
                Membership.organization_id == membership.organization_id
            )
        )
        seats = int(seat_count or 1)

    session = await anyio.to_thread.run_sync(
        lambda: stripe_service.create_checkout_session(
            user_id=str(current_user.id),
            user_email=current_user.email,
            stripe_customer_id=current_user.stripe_customer_id,
            organization_id=org_id,
            seats=seats,
        )
    )

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


# ── GET /portal ────────────────────────────────────────────────────────────────

@router.get(
    "/portal",
    response_model=PortalResponse,
    summary="Return Stripe Customer Portal URL for subscription management",
    dependencies=[
        # 10 portal sessions / hour / IP
        Depends(RateLimitCheck("billing:portal", max_per_ip=10, window_seconds=3600)),
    ],
)
async def get_portal(current_user: CurrentUser) -> PortalResponse:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Complete a checkout first.",
        )

    portal = await anyio.to_thread.run_sync(
        lambda: stripe_service.create_customer_portal_session(
            stripe_customer_id=current_user.stripe_customer_id,
        )
    )
    return PortalResponse(portal_url=portal.url)


# ── GET /status ────────────────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=BillingStatusResponse,
    summary="Get current user billing status and plan",
)
async def get_billing_status(current_user: CurrentUser) -> BillingStatusResponse:
    sub_info: dict = {"status": None, "current_period_end": None, "cancel_at_period_end": None}

    if current_user.stripe_customer_id and settings.STRIPE_SECRET_KEY:
        try:
            sub_info = await anyio.to_thread.run_sync(
                lambda: stripe_service.get_subscription_status(
                    current_user.stripe_customer_id
                )
            )
        except Exception as exc:
            logger.warning("Could not fetch subscription status: %s", exc)

    return BillingStatusResponse(
        plan=current_user.plan,
        stripe_customer_id=current_user.stripe_customer_id,
        subscription_status=sub_info.get("status"),
        current_period_end=sub_info.get("current_period_end"),
        cancel_at_period_end=sub_info.get("cancel_at_period_end"),
    )


# ── POST /webhook ──────────────────────────────────────────────────────────────

@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook receiver (signature-verified, no auth header)",
    include_in_schema=False,
)
async def stripe_webhook(
    request: Request,
    db: DB,
    stripe_signature: str = Header(alias="stripe-signature", default=""),
) -> dict:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    # Fail fast on missing signature header — gives a clearer 400 than letting
    # the Stripe SDK raise SignatureVerificationError on an empty string, and
    # surfaces an audit event so unsigned probes are visible in security logs.
    if not stripe_signature:
        from app.core.audit_log import log_security_event

        log_security_event(
            "webhook_missing_signature",
            user_id=None,
            detail={"remote": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()

    try:
        event = await anyio.to_thread.run_sync(
            lambda: stripe_service.construct_webhook_event(payload, stripe_signature)
        )
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as exc:
        logger.error("Webhook parse error: %s", exc)
        raise HTTPException(status_code=400, detail="Bad webhook payload")

    # Stripe SDK ≥10 returns a stripe.Event object (attribute access, no .get()).
    # Normalise the whole payload to a plain dict once so the rest of the
    # handler can keep using .get() chains without per-line type checks.
    if hasattr(event, "to_dict_recursive"):
        event = event.to_dict_recursive()
    elif hasattr(event, "to_dict"):
        event = event.to_dict()

    event_id: str = event.get("id", "")
    event_type: str = event["type"]

    # ── Idempotency check ──────────────────────────────────────────────────────
    # Stripe retries webhooks for up to 3 days on non-2xx responses.
    # Without idempotency protection, a retry storm (or a bug) could upgrade /
    # downgrade users multiple times for the same payment event.
    #
    # Strategy: store processed event IDs in Redis with a 24-hour TTL.
    # 24h matches Stripe's retry window — after that, a duplicate event would
    # be a legitimate re-send worth processing again.
    if event_id:
        from app.core.audit_log import log_security_event
        from app.core.cache import cache
        from app.core.security_config import security_settings

        idempotency_key = f"webhook:stripe:{event_id}"
        already_processed = await cache.get(idempotency_key)
        if already_processed:
            log_security_event(
                "webhook_replay_blocked",
                user_id=None,
                detail={"event_id": event_id, "event_type": event_type},
            )
            logger.info("Stripe webhook %s already processed — returning 200 (idempotent)", event_id)
            return {"received": True, "idempotent": True}

    logger.info("Stripe webhook received: %s id=%s", event_type, event_id)

    # ── checkout.session.completed ─────────────────────────────────────────────
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if user_id:
            upgraded = await _upgrade_user(
                db=db,
                user_id=user_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                plan=Plan.PRO,
            )
            # Fire-and-forget welcome-to-Pro email. Best-effort: a Celery
            # outage must not 5xx the webhook (Stripe would retry and we'd
            # double-process). We dispatch and log; failures are caught.
            if upgraded is not None:
                try:
                    from app.workers.tasks.send_email import send_email_task

                    send_email_task.delay(
                        to=upgraded.email,
                        template_name="plan_changed",
                        params={"name": upgraded.name or "", "new_plan": "pro"},
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("post_checkout_email_dispatch_failed: %s", exc)

    # ── invoice.paid — renew / confirm active subscription ─────────────────────
    elif event_type == "invoice.paid":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")
        period_end = invoice.get("lines", {}).get("data", [{}])[0].get(
            "period", {}
        ).get("end")

        if customer_id:
            await _renew_user(
                db=db,
                customer_id=customer_id,
                subscription_id=subscription_id,
                period_end=period_end,
            )

    # ── customer.subscription.deleted — cancel / downgrade ─────────────────────
    elif event_type in (
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ):
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        if customer_id:
            await _downgrade_user(db=db, customer_id=customer_id)

    # ── customer.subscription.updated — handle plan changes ────────────────────
    elif event_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        sub_status = sub.get("status")

        if customer_id and sub_status in ("active", "trialing"):
            # Re-confirm pro (handles reactivation after cancel).
            # B10: also mirror onto the org so re-activated subs restore
            # team access, not just the individual paying user.
            user = await _get_user_by_customer(db, customer_id)
            if user and user.plan != Plan.PRO:
                user.plan = Plan.PRO
                await _sync_org_billing(db, user, plan=Plan.PRO)
                logger.info("Re-activated pro for customer %s", customer_id)

        elif customer_id and sub_status in ("canceled", "unpaid", "past_due"):
            await _downgrade_user(db=db, customer_id=customer_id)

    # ── v3.0.1 — fan out subscription.changed to user webhooks ────────────────
    if event_type in (
        "customer.subscription.deleted",
        "customer.subscription.paused",
        "customer.subscription.updated",
        "invoice.payment_succeeded",
    ):
        try:
            sub_obj = event["data"]["object"]
            customer_id = sub_obj.get("customer")
            if customer_id:
                user = await _get_user_by_customer(db, customer_id)
                if user:
                    from app.services.webhooks import emit as emit_webhook
                    await emit_webhook(
                        db,
                        user.id,
                        "subscription.changed",
                        {
                            "stripe_event": event_type,
                            "plan": user.plan,
                            "status": sub_obj.get("status"),
                        },
                    )
        except Exception as wh_exc:
            logger.warning("subscription.changed webhook emit failed: %s", wh_exc)

    # ── Mark event as processed in Redis (idempotency) ────────────────────────
    # Write AFTER processing so a crash before completion doesn't lock out retries.
    if event_id:
        await cache.set(
            idempotency_key,
            {"event_type": event_type, "processed": True},
            ttl=security_settings.WEBHOOK_IDEMPOTENCY_TTL_SECONDS,
        )

    return {"received": True}


# ── DB helpers ─────────────────────────────────────────────────────────────────

async def _get_user_by_id(db: DB, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_user_by_customer(db: DB, customer_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    return result.scalar_one_or_none()


# B10 fix: keep Organization rows in lockstep with User billing state.
# Before v2.0 the User was the billing entity; after v2.0 the
# Organization owns the subscription. The webhook had not been updated
# yet, so cancellations downgraded the paying user but every other
# member of their org kept Pro access via Organization.plan = "pro".
#
# Strategy: every helper that mutates User billing state also resolves
# the user's primary org (via membership), mirrors plan / stripe_* on
# the org row, and logs both writes. The Membership lookup picks the
# first org the user belongs to — for personal orgs that's a 1:1
# mapping; for team orgs the owner's personal org gets billed.

async def _get_org_for_user(db: DB, user_id) -> "Organization | None":  # noqa: F821
    from sqlalchemy import select as _select

    from app.models.organization import Membership, Organization

    result = await db.execute(
        _select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user_id)
        .order_by(Organization.is_personal.desc(), Organization.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _sync_org_billing(
    db: DB,
    user,
    *,
    plan: str | None = None,
    customer_id: str | None = None,
    subscription_id: str | None | bool = False,  # False = no-op, None = clear
) -> None:
    """Mirror billing fields onto the user's primary org.

    `subscription_id`: False = leave unchanged, None = clear, str = set.
    Tri-state because the webhook needs to clear the field on cancellation
    but leave it alone on a simple renewal.
    """
    org = await _get_org_for_user(db, user.id)
    if not org:
        return
    if plan is not None:
        org.plan = plan.value if isinstance(plan, Plan) else plan
    if customer_id and not org.stripe_customer_id:
        org.stripe_customer_id = customer_id
    if subscription_id is not False:
        org.stripe_subscription_id = subscription_id
    logger.info("org_billing_synced org=%s plan=%s", org.id, org.plan)


async def _upgrade_user(
    db: DB,
    user_id: str,
    customer_id: str | None,
    subscription_id: str | None,
    plan: str,
) -> User | None:
    user = await _get_user_by_id(db, user_id)
    if not user:
        logger.warning("Webhook: user %s not found for upgrade", user_id)
        return None

    user.plan = plan.value if isinstance(plan, Plan) else plan
    if customer_id:
        user.stripe_customer_id = customer_id
    if subscription_id:
        user.stripe_subscription_id = subscription_id

    await _sync_org_billing(
        db, user, plan=plan, customer_id=customer_id, subscription_id=subscription_id,
    )
    logger.info("Upgraded user %s to %s", user_id, plan)
    return user


async def _renew_user(
    db: DB,
    customer_id: str,
    subscription_id: str | None,
    period_end: int | None,
) -> None:
    user = await _get_user_by_customer(db, customer_id)
    if not user:
        return

    user.plan = Plan.PRO
    if subscription_id:
        user.stripe_subscription_id = subscription_id
    if period_end:
        user.plan_expires_at = datetime.fromtimestamp(period_end, tz=UTC)

    await _sync_org_billing(
        db, user, plan=Plan.PRO, subscription_id=subscription_id,
    )
    logger.info("Renewed pro for customer %s until %s", customer_id, period_end)


async def _downgrade_user(db: DB, customer_id: str) -> None:
    user = await _get_user_by_customer(db, customer_id)
    if not user:
        return

    user.plan = Plan.FREE
    user.stripe_subscription_id = None
    user.plan_expires_at = None

    # Tri-state: pass None to actively clear the org's subscription_id —
    # otherwise we'd leave a dangling reference to a cancelled Stripe sub.
    await _sync_org_billing(db, user, plan=Plan.FREE, subscription_id=None)
    logger.info("Downgraded customer %s to free", customer_id)
