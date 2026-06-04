"""Integration tests for the portfolio custom-domain routes (v1.2.1)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.models.portfolio import Portfolio
from app.models.user import User
from app.security import get_current_user
from app.services import domain_verification as dv


def _make_user(plan: str, seed: int = 1) -> User:
    u = User.__new__(User)
    u.id = uuid.UUID(f"00000000-0000-0000-0000-{seed:012d}")
    u.clerk_user_id = f"clerk_{seed}"
    u.email = f"u{seed}@example.com"
    u.name = f"User {seed}"
    u.plan = plan
    u.avatar_url = None
    u.stripe_customer_id = None
    u.stripe_subscription_id = None
    u.plan_expires_at = None
    u.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    u.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


async def _client_as(user: User, db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    )


async def _make_portfolio(db_session: AsyncSession, owner: User, slug: str) -> Portfolio:
    p = Portfolio(
        user_id=owner.id,
        resume_id=None,
        slug=slug,
        template_id="aurora",
        content={},
        status="completed",
        is_public=True,
        views=0,
    )
    db_session.add(p)
    await db_session.flush()
    return p


_VERIFIED = dv.VerificationResult(
    domain="alex.dev",
    verified=True,
    cname_target=dv.CUSTOM_DOMAIN_TARGET,
    expected_target=dv.CUSTOM_DOMAIN_TARGET,
    detail="ok",
)
_UNVERIFIED = dv.VerificationResult(
    domain="alex.dev",
    verified=False,
    cname_target="elsewhere.example",
    expected_target=dv.CUSTOM_DOMAIN_TARGET,
    detail="wrong target",
)


def _patch_cache():
    from unittest.mock import AsyncMock
    return [
        patch("app.core.cache.cache.get", new_callable=AsyncMock, return_value=None),
        patch("app.core.cache.cache.set", new_callable=AsyncMock),
        patch("app.core.cache.cache.delete", new_callable=AsyncMock),
    ]


class TestAttachCustomDomain:
    async def test_free_user_blocked(self, db_session: AsyncSession):
        free = _make_user("free")
        p = await _make_portfolio(db_session, free, "p-aaaaaaaa")

        async with await _client_as(free, db_session) as ac:
            r = await ac.put(
                f"/api/v1/portfolio/{p.id}/custom-domain",
                json={"domain": "alex.dev"},
            )
        app.dependency_overrides.clear()
        assert r.status_code == 403
        assert r.json()["error_code"] == "PLAN_LIMIT_EXCEEDED"

    async def test_pro_user_attaches_and_runs_verification(
        self, db_session: AsyncSession
    ):
        pro = _make_user("pro", seed=2)
        p = await _make_portfolio(db_session, pro, "p-bbbbbbbb")

        patches = _patch_cache()
        for ctx in patches:
            ctx.__enter__()
        try:
            with patch(
                "app.services.domain_verification.verify_cname",
                return_value=_VERIFIED,
            ):
                async with await _client_as(pro, db_session) as ac:
                    r = await ac.put(
                        f"/api/v1/portfolio/{p.id}/custom-domain",
                        json={"domain": "https://Alex.dev/"},
                    )
        finally:
            for ctx in patches:
                ctx.__exit__(None, None, None)
        app.dependency_overrides.clear()

        assert r.status_code == 200
        body = r.json()
        assert body["domain"] == "alex.dev"  # normalized
        assert body["verified"] is True

        await db_session.refresh(p)
        assert p.custom_domain == "alex.dev"

    async def test_invalid_domain_rejected(self, db_session: AsyncSession):
        pro = _make_user("pro", seed=3)
        p = await _make_portfolio(db_session, pro, "p-cccccccc")

        async with await _client_as(pro, db_session) as ac:
            r = await ac.put(
                f"/api/v1/portfolio/{p.id}/custom-domain",
                json={"domain": "not a domain"},
            )
        app.dependency_overrides.clear()
        assert r.status_code == 400

    async def test_reserved_suffix_rejected(self, db_session: AsyncSession):
        pro = _make_user("pro", seed=4)
        p = await _make_portfolio(db_session, pro, "p-dddddddd")

        async with await _client_as(pro, db_session) as ac:
            r = await ac.put(
                f"/api/v1/portfolio/{p.id}/custom-domain",
                json={"domain": "anything.vyroportify.com"},
            )
        app.dependency_overrides.clear()
        assert r.status_code == 400

    async def test_duplicate_domain_returns_409(self, db_session: AsyncSession):
        pro_a = _make_user("pro", seed=5)
        pro_b = _make_user("pro", seed=6)

        p_a = await _make_portfolio(db_session, pro_a, "p-eeeeeeee")
        p_a.custom_domain = "taken.dev"
        p_b = await _make_portfolio(db_session, pro_b, "p-ffffffff")
        await db_session.flush()

        patches = _patch_cache()
        for ctx in patches:
            ctx.__enter__()
        try:
            async with await _client_as(pro_b, db_session) as ac:
                r = await ac.put(
                    f"/api/v1/portfolio/{p_b.id}/custom-domain",
                    json={"domain": "TAKEN.dev"},
                )
        finally:
            for ctx in patches:
                ctx.__exit__(None, None, None)
        app.dependency_overrides.clear()

        assert r.status_code == 409


class TestGetCustomDomainStatus:
    async def test_returns_unattached_when_none(self, db_session: AsyncSession):
        pro = _make_user("pro", seed=7)
        p = await _make_portfolio(db_session, pro, "p-gggggggg")

        async with await _client_as(pro, db_session) as ac:
            r = await ac.get(f"/api/v1/portfolio/{p.id}/custom-domain")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        body = r.json()
        assert body["domain"] is None
        assert body["verified"] is False

    async def test_runs_live_verification_when_attached(
        self, db_session: AsyncSession
    ):
        pro = _make_user("pro", seed=8)
        p = await _make_portfolio(db_session, pro, "p-hhhhhhhh")
        p.custom_domain = "alex.dev"
        await db_session.flush()

        with patch(
            "app.services.domain_verification.verify_cname",
            return_value=_UNVERIFIED,
        ):
            async with await _client_as(pro, db_session) as ac:
                r = await ac.get(f"/api/v1/portfolio/{p.id}/custom-domain")
        app.dependency_overrides.clear()

        assert r.status_code == 200
        body = r.json()
        assert body["domain"] == "alex.dev"
        assert body["verified"] is False
        assert body["cname_target"] == "elsewhere.example"


class TestDetachCustomDomain:
    async def test_clears_field(self, db_session: AsyncSession):
        pro = _make_user("pro", seed=9)
        p = await _make_portfolio(db_session, pro, "p-iiiiiiii")
        p.custom_domain = "alex.dev"
        await db_session.flush()

        patches = _patch_cache()
        for ctx in patches:
            ctx.__enter__()
        try:
            async with await _client_as(pro, db_session) as ac:
                r = await ac.delete(f"/api/v1/portfolio/{p.id}/custom-domain")
        finally:
            for ctx in patches:
                ctx.__exit__(None, None, None)
        app.dependency_overrides.clear()

        assert r.status_code == 200
        await db_session.refresh(p)
        assert p.custom_domain is None
