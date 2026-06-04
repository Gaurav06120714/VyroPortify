"""Cross-tenant isolation regression tests (v1.1.0).

Verify that user B cannot read, modify, or delete resources owned by user A.
Every owner-scoped endpoint must return 404 (not 403) on a foreign resource.
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.database import get_db
from app.main import app
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.models.user import User
from app.security import get_current_user


def _make_user(seed: int) -> User:
    u = User.__new__(User)
    u.id = uuid.UUID(f"00000000-0000-0000-0000-{seed:012d}")
    u.clerk_user_id = f"clerk_user_{seed}"
    u.email = f"user{seed}@example.com"
    u.name = f"User {seed}"
    u.plan = "free"
    u.avatar_url = None
    u.stripe_customer_id = None
    u.stripe_subscription_id = None
    u.plan_expires_at = None
    u.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    u.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


@pytest.fixture
def user_a() -> User:
    return _make_user(1)


@pytest.fixture
def user_b() -> User:
    return _make_user(2)


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


class TestCrossTenantPortfolioIsolation:
    async def test_user_b_cannot_read_user_a_portfolio_status(
        self, db_session: AsyncSession, user_a: User, user_b: User
    ):
        portfolio = Portfolio(
            user_id=user_a.id,
            resume_id=None,
            slug="a-portfolio-aaaaaaaa",
            template_id="aurora",
            content={},
            status="completed",
            is_public=False,
            views=0,
        )
        db_session.add(portfolio)
        await db_session.flush()

        with patch("app.core.cache.cache.get", new_callable=AsyncMock, return_value=None), \
             patch("app.core.cache.cache.set", new_callable=AsyncMock), \
             patch("app.core.cache.cache.delete", new_callable=AsyncMock):
            async with await _client_as(user_b, db_session) as ac:
                r = await ac.get(f"/api/v1/portfolio/{portfolio.id}/status")
            app.dependency_overrides.clear()

        # Must be 404 (not 403) to avoid leaking resource existence.
        assert r.status_code == 404

    async def test_user_b_cannot_delete_user_a_portfolio(
        self, db_session: AsyncSession, user_a: User, user_b: User
    ):
        portfolio = Portfolio(
            user_id=user_a.id,
            resume_id=None,
            slug="del-portfolio-aaaaaaaa",
            template_id="aurora",
            content={},
            status="completed",
            is_public=False,
            views=0,
        )
        db_session.add(portfolio)
        await db_session.flush()
        portfolio_id = portfolio.id

        with patch("app.core.cache.cache.get", new_callable=AsyncMock, return_value=None), \
             patch("app.core.cache.cache.set", new_callable=AsyncMock), \
             patch("app.core.cache.cache.delete", new_callable=AsyncMock):
            async with await _client_as(user_b, db_session) as ac:
                r = await ac.delete(f"/api/v1/portfolio/{portfolio_id}")
            app.dependency_overrides.clear()

        assert r.status_code == 404

        # Resource still exists — confirms 404 was authz, not a real delete.
        from sqlalchemy import select
        result = await db_session.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        assert result.scalar_one_or_none() is not None

    async def test_user_b_cannot_toggle_publish_on_user_a_portfolio(
        self, db_session: AsyncSession, user_a: User, user_b: User
    ):
        portfolio = Portfolio(
            user_id=user_a.id,
            resume_id=None,
            slug="pub-portfolio-aaaaaaaa",
            template_id="aurora",
            content={},
            status="completed",
            is_public=False,
            views=0,
        )
        db_session.add(portfolio)
        await db_session.flush()

        with patch("app.core.cache.cache.get", new_callable=AsyncMock, return_value=None), \
             patch("app.core.cache.cache.set", new_callable=AsyncMock), \
             patch("app.core.cache.cache.delete", new_callable=AsyncMock):
            async with await _client_as(user_b, db_session) as ac:
                r = await ac.put(
                    f"/api/v1/portfolio/{portfolio.id}/publish",
                    json={"is_public": True},
                )
            app.dependency_overrides.clear()

        assert r.status_code == 404


class TestCrossTenantResumeIsolation:
    async def test_user_b_cannot_read_user_a_resume_status(
        self, db_session: AsyncSession, user_a: User, user_b: User
    ):
        resume = Resume(
            user_id=user_a.id,
            original_filename="a.pdf",
            s3_key=None,
            file_size=0,
            mime_type="application/pdf",
            status="completed",
            parsed_data={"full_name": "A"},
        )
        db_session.add(resume)
        await db_session.flush()

        async with await _client_as(user_b, db_session) as ac:
            r = await ac.get(f"/api/v1/resume/{resume.id}/status")
        app.dependency_overrides.clear()

        assert r.status_code == 404

    async def test_user_b_cannot_delete_user_a_resume(
        self, db_session: AsyncSession, user_a: User, user_b: User
    ):
        resume = Resume(
            user_id=user_a.id,
            original_filename="a.pdf",
            s3_key=None,
            file_size=0,
            mime_type="application/pdf",
            status="completed",
            parsed_data={"full_name": "A"},
        )
        db_session.add(resume)
        await db_session.flush()
        resume_id = resume.id

        async with await _client_as(user_b, db_session) as ac:
            r = await ac.delete(f"/api/v1/resume/{resume_id}")
        app.dependency_overrides.clear()

        assert r.status_code == 404

        from sqlalchemy import select
        result = await db_session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        assert result.scalar_one_or_none() is not None
