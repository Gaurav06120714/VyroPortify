"""Stripe service — checkout, portal, webhook handling.

All Stripe SDK calls are synchronous (stripe-python is sync).
Wrap in anyio.to_thread.run_sync() when calling from async FastAPI handlers.
"""

import logging
from typing import Any

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialise the SDK once at import time — thread-safe singleton
stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Checkout ───────────────────────────────────────────────────────────────────

def create_checkout_session(
    user_id: str,
    user_email: str,
    stripe_customer_id: str | None = None,
    *,
    organization_id: str | None = None,
    seats: int = 1,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout session for the Pro plan.

    v2.0.4 introduces per-seat pricing. `seats` defaults to 1 so existing
    single-user checkouts behave identically; pass seats=N when checking
    out for a team org. The Stripe price referenced by
    STRIPE_PRO_PRICE_ID must be configured as recurring/per_unit so the
    `quantity` field is respected.

    Returns the full Session object; call .url to get the redirect URL.
    """
    seats = max(1, int(seats))

    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [
            {
                "price": settings.STRIPE_PRO_PRICE_ID,
                "quantity": seats,
                # Allow quantity adjustments from Stripe's hosted page so
                # the customer can resize their seat count at checkout.
                "adjustable_quantity": {
                    "enabled": True,
                    "minimum": 1,
                    "maximum": 200,
                },
            }
        ],
        "success_url": f"{settings.FRONTEND_URL}/dashboard/settings/billing?session_id={{CHECKOUT_SESSION_ID}}&success=1",
        "cancel_url": f"{settings.FRONTEND_URL}/pricing?cancelled=1",
        "metadata": {
            "user_id": user_id,
            **({"organization_id": organization_id} if organization_id else {}),
        },
        "subscription_data": {
            "metadata": {
                "user_id": user_id,
                **({"organization_id": organization_id} if organization_id else {}),
            },
        },
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
    }

    if stripe_customer_id:
        # Re-use existing customer so payment methods are pre-filled
        params["customer"] = stripe_customer_id
    else:
        params["customer_email"] = user_email

    session = stripe.checkout.Session.create(**params)
    logger.info(
        "Created checkout session %s for user %s seats=%d org=%s",
        session.id, user_id, seats, organization_id,
    )
    return session


# ── Customer portal ────────────────────────────────────────────────────────────

def create_customer_portal_session(
    stripe_customer_id: str,
    return_url: str | None = None,
) -> stripe.billing_portal.Session:
    """
    Create a Stripe Billing Portal session so the user can manage their subscription.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url or f"{settings.FRONTEND_URL}/dashboard/settings/billing",
    )
    logger.info("Created portal session for customer %s", stripe_customer_id)
    return session


# ── Webhook verification ───────────────────────────────────────────────────────

def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify the Stripe-Signature header and return a typed Event object.
    Raises stripe.error.SignatureVerificationError on mismatch.
    """
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


# ── Customer helpers ───────────────────────────────────────────────────────────

def get_or_create_customer(user_id: str, email: str, name: str | None = None) -> str:
    """
    Look up an existing Stripe customer by metadata user_id, or create one.
    Returns the stripe_customer_id string.
    """
    existing = stripe.Customer.search(
        query=f'metadata["user_id"]:"{user_id}"',
        limit=1,
    )
    if existing.data:
        return existing.data[0].id

    customer = stripe.Customer.create(
        email=email,
        name=name,
        metadata={"user_id": user_id},
    )
    return customer.id


def get_subscription_status(stripe_customer_id: str) -> dict[str, Any]:
    """
    Returns the current subscription plan for a customer.
    dict keys: status, plan, current_period_end, cancel_at_period_end
    """
    subscriptions = stripe.Subscription.list(
        customer=stripe_customer_id,
        status="active",
        limit=1,
        expand=["data.items.data.price.product"],
    )

    if not subscriptions.data:
        # Check for trialing subscriptions too
        trialing = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="trialing",
            limit=1,
            expand=["data.items.data.price.product"],
        )
        if not trialing.data:
            return {"status": "none", "plan": "free"}
        sub = trialing.data[0]
    else:
        sub = subscriptions.data[0]

    return {
        "status": sub.status,
        "plan": "pro",
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "subscription_id": sub.id,
    }
