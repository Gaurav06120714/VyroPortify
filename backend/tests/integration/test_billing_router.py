"""Integration tests for the billing router.

Covers: create-checkout, webhook idempotency, webhook invalid sig, billing status.
Stripe and Redis are fully mocked — no real external calls.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ── Stripe mock helpers ────────────────────────────────────────────────────────

def _make_checkout_session(
    session_id: str = "cs_test_abc123",
    checkout_url: str = "https://checkout.stripe.com/pay/cs_test_abc123",
) -> MagicMock:
    session = MagicMock()
    session.id = session_id
    session.url = checkout_url
    return session


def _make_webhook_event(
    event_id: str = "evt_test_001",
    event_type: str = "checkout.session.completed",
    user_id: str = "00000000-0000-0000-0000-000000000001",
    customer_id: str = "cus_test_001",
    subscription_id: str = "sub_test_001",
) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "data": {
            "object": {
                "metadata": {"user_id": user_id},
                "customer": customer_id,
                "subscription": subscription_id,
            }
        },
    }


class TestCreateCheckout:
    @patch("app.routers.billing.stripe_service")
    @patch("app.routers.billing.settings")
    async def test_create_checkout_session_returns_url(
        self,
        mock_settings,
        mock_stripe_svc,
        client: AsyncClient,
        auth_headers: dict,
        fake_user,
    ):
        """POST /billing/create-checkout should return checkout_url and session_id."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_PRO_PRICE_ID = "price_test"
        mock_settings.FRONTEND_URL = "http://localhost:3000"

        # User is on free plan (fake_user.plan = "free")
        fake_user.plan = "free"
        fake_user.stripe_customer_id = "cus_existing_123"

        mock_stripe_svc.create_checkout_session.return_value = _make_checkout_session()

        import anyio

        with patch("app.routers.billing.anyio.to_thread.run_sync") as mock_run:
            mock_run.return_value = _make_checkout_session()
            response = await client.post(
                "/api/v1/billing/create-checkout",
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data

    @patch("app.routers.billing.settings")
    async def test_create_checkout_already_pro_returns_400(
        self,
        mock_settings,
        client: AsyncClient,
        auth_headers: dict,
        fake_pro_user,
    ):
        """A Pro user trying to checkout should get 400 'already on Pro plan'."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"

        # Override current user to be the pro user
        from app.security import get_current_user
        from app.main import app

        async def override_pro():
            return fake_pro_user

        app.dependency_overrides[get_current_user] = override_pro

        response = await client.post(
            "/api/v1/billing/create-checkout",
            headers=auth_headers,
        )
        # Restore
        from tests.conftest import fake_user as _
        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @patch("app.routers.billing.settings")
    async def test_create_checkout_stripe_not_configured_returns_503(
        self,
        mock_settings,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """When STRIPE_SECRET_KEY is empty, should return 503."""
        mock_settings.STRIPE_SECRET_KEY = ""
        response = await client.post(
            "/api/v1/billing/create-checkout",
            headers=auth_headers,
        )
        assert response.status_code == 503


class TestStripeWebhook:
    @patch("app.routers.billing.stripe_service")
    @patch("app.routers.billing.settings")
    @patch("app.core.cache.cache.get", new_callable=AsyncMock, return_value=None)
    @patch("app.core.cache.cache.set", new_callable=AsyncMock)
    async def test_stripe_webhook_processes_pro_upgrade(
        self,
        mock_cache_set,
        mock_cache_get,
        mock_settings,
        mock_stripe_svc,
        client: AsyncClient,
        db_session: AsyncSession,
        fake_user,
    ):
        """A valid checkout.session.completed webhook should upgrade the user to Pro."""
        from app.models.user import User

        # Persist the fake user to the DB so the webhook can find them
        user = User(
            id=fake_user.id,
            clerk_user_id=fake_user.clerk_user_id,
            email=fake_user.email,
            name=fake_user.name,
            plan="free",
        )
        db_session.add(user)
        await db_session.flush()

        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

        event = _make_webhook_event(user_id=str(fake_user.id))
        mock_stripe_svc.construct_webhook_event.return_value = event

        import anyio

        with patch("app.routers.billing.anyio.to_thread.run_sync") as mock_run:
            mock_run.return_value = event
            response = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event),
                headers={"stripe-signature": "t=123,v1=abc123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["received"] is True

    @patch("app.routers.billing.settings")
    @patch("app.core.cache.cache.get", new_callable=AsyncMock)
    async def test_stripe_webhook_idempotency_skips_duplicate(
        self,
        mock_cache_get,
        mock_settings,
        client: AsyncClient,
    ):
        """When cache returns a processed event, the webhook should return idempotent=True."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

        # Simulate the event was already processed (cache returns a value)
        mock_cache_get.return_value = {"event_type": "checkout.session.completed", "processed": True}

        event = _make_webhook_event()

        import anyio

        with patch("app.routers.billing.anyio.to_thread.run_sync") as mock_run:
            mock_run.return_value = event
            response = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event),
                headers={"stripe-signature": "t=123,v1=abc123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data.get("idempotent") is True

    @patch("app.routers.billing.settings")
    async def test_stripe_webhook_invalid_signature_returns_400(
        self,
        mock_settings,
        client: AsyncClient,
    ):
        """Invalid Stripe signature should return 400."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

        import anyio

        with patch("app.routers.billing.anyio.to_thread.run_sync") as mock_run:
            mock_run.side_effect = stripe.SignatureVerificationError(
                "Invalid signature",
                sig_header="bad-sig",
            )
            response = await client.post(
                "/api/v1/billing/webhook",
                content=b"{}",
                headers={"stripe-signature": "invalid-sig"},
            )

        assert response.status_code == 400

    @patch("app.routers.billing.settings")
    async def test_stripe_webhook_missing_signature_returns_400(
        self,
        mock_settings,
        client: AsyncClient,
    ):
        """Webhook without a stripe-signature header must be rejected fast."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_123"

        response = await client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
            # No stripe-signature header at all.
        )

        assert response.status_code == 400
        assert "signature" in response.json().get("detail", "").lower()

    @patch("app.routers.billing.settings")
    async def test_stripe_webhook_not_configured_returns_503(
        self,
        mock_settings,
        client: AsyncClient,
    ):
        mock_settings.STRIPE_WEBHOOK_SECRET = ""
        response = await client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=123,v1=abc123"},
        )
        assert response.status_code == 503


class TestBillingStatus:
    @patch("app.routers.billing.settings")
    async def test_billing_status_returns_plan(
        self,
        mock_settings,
        client: AsyncClient,
        auth_headers: dict,
        fake_user,
    ):
        """GET /billing/status should return the user's plan and billing info."""
        mock_settings.STRIPE_SECRET_KEY = ""  # no Stripe → skip subscription check
        mock_settings.STRIPE_WEBHOOK_SECRET = ""

        response = await client.get("/api/v1/billing/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == fake_user.plan
        assert "stripe_customer_id" in data
        assert "subscription_status" in data

    @patch("app.routers.billing.stripe_service")
    @patch("app.routers.billing.settings")
    async def test_billing_status_with_stripe_returns_subscription_info(
        self,
        mock_settings,
        mock_stripe_svc,
        client: AsyncClient,
        auth_headers: dict,
        fake_pro_user,
    ):
        """When Stripe is configured and user has customer ID, should return sub status."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"

        from app.security import get_current_user
        from app.main import app

        async def override_pro():
            return fake_pro_user

        app.dependency_overrides[get_current_user] = override_pro

        mock_stripe_svc.get_subscription_status.return_value = {
            "status": "active",
            "current_period_end": 1735689600,
            "cancel_at_period_end": False,
        }

        with patch("app.routers.billing.anyio.to_thread.run_sync") as mock_run:
            mock_run.return_value = {
                "status": "active",
                "current_period_end": 1735689600,
                "cancel_at_period_end": False,
            }
            response = await client.get("/api/v1/billing/status", headers=auth_headers)

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
