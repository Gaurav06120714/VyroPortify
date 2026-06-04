"""Stripe Connect router (v2.1.1).

Template authors who want to sell paid templates onboard a Stripe
Express account here. We store the connected account id on the User
row (column added by alembic 0011 below) and proxy a one-time
account-link URL so the user finishes onboarding on Stripe's hosted
flow.

Revenue split is 85% author / 15% platform via `application_fee_amount`
on each Checkout session — set in stripe_service when a paid template
checkout is initiated (separate sub-version because that flow
intersects with portfolio generation, not just the marketplace).
"""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.database import DB
from app.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connect", tags=["Connect"])


class OnboardResponse(BaseModel):
    onboarding_url: str
    account_id: str


@router.post(
    "/onboard",
    response_model=OnboardResponse,
    summary="Create or refresh a Stripe Express account for the caller",
)
async def onboard(current_user: CurrentUser, db: DB) -> OnboardResponse:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    account_id = getattr(current_user, "stripe_account_id", None)
    if not account_id:
        # Express account: hosted onboarding, light KYC, fastest path
        # for individual authors. Country defaulted to US — extend via
        # a request body parameter when we expand the marketplace
        # internationally.
        account = stripe.Account.create(
            type="express",
            email=current_user.email,
            metadata={"user_id": str(current_user.id)},
        )
        account_id = account.id
        current_user.stripe_account_id = account_id
        await db.commit()
        logger.info("connect_account_created user=%s account=%s", current_user.id, account_id)

    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=f"{settings.FRONTEND_URL}/dashboard/settings/payouts?refresh=1",
        return_url=f"{settings.FRONTEND_URL}/dashboard/settings/payouts?done=1",
        type="account_onboarding",
    )
    return OnboardResponse(onboarding_url=link.url, account_id=account_id)


@router.get(
    "/status",
    summary="Return Stripe Connect onboarding state for the caller",
)
async def connect_status(current_user: CurrentUser) -> dict:
    if not settings.STRIPE_SECRET_KEY:
        return {"configured": False}
    account_id = getattr(current_user, "stripe_account_id", None)
    if not account_id:
        return {"configured": False, "account_id": None}

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        account = stripe.Account.retrieve(account_id)
    except stripe.error.StripeError as exc:
        logger.warning("connect_status_fetch_failed user=%s err=%s", current_user.id, exc)
        return {"configured": True, "account_id": account_id, "details_submitted": False}

    return {
        "configured": True,
        "account_id": account_id,
        "details_submitted": bool(account.details_submitted),
        "payouts_enabled": bool(account.payouts_enabled),
        "charges_enabled": bool(account.charges_enabled),
    }
