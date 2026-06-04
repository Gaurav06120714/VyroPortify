"""Plan-gating regression tests (v1.1.1).

Pro-only endpoints must reject free users with 403 PLAN_LIMIT_EXCEEDED and
must let Pro users through (we only check that the gate passes, not the AI
side-effect).
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.models.user import User
from app.security import get_current_user


def _make_user(plan: str) -> User:
    u = User.__new__(User)
    u.id = uuid.UUID("00000000-0000-0000-0000-000000000099")
    u.clerk_user_id = "clerk_plan_test"
    u.email = "plan@example.com"
    u.name = "Plan Tester"
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


_SUGGEST_PAYLOAD = {
    "career_goal": "senior engineer",
    "role_titles": ["Backend Engineer"],
    "tech_stack": ["Python"],
    "current_skills": ["FastAPI"],
}

_COVER_LETTER_PAYLOAD = {
    "name": "Test User",
    "title": "Engineer",
    "company": "Acme",
    "role": "Senior Engineer",
    "highlights": "Built things.",
    "tone": "professional",
}


class TestPlanGatingFreeRejected:
    async def test_free_user_blocked_from_suggest_skills(
        self, db_session: AsyncSession
    ):
        free_user = _make_user("free")
        async with await _client_as(free_user, db_session) as ac:
            r = await ac.post("/api/v1/resume/suggest-skills", json=_SUGGEST_PAYLOAD)
        app.dependency_overrides.clear()

        assert r.status_code == 403
        body = r.json()
        assert body["error_code"] == "PLAN_LIMIT_EXCEEDED"

    async def test_free_user_blocked_from_cover_letter(
        self, db_session: AsyncSession
    ):
        free_user = _make_user("free")
        async with await _client_as(free_user, db_session) as ac:
            r = await ac.post("/api/v1/resume/cover-letter", json=_COVER_LETTER_PAYLOAD)
        app.dependency_overrides.clear()

        assert r.status_code == 403
        body = r.json()
        assert body["error_code"] == "PLAN_LIMIT_EXCEEDED"


class TestPlanGatingProAllowed:
    async def test_pro_user_passes_suggest_skills_gate(
        self, db_session: AsyncSession
    ):
        pro_user = _make_user("pro")
        # Mock AI so we don't hit the network — we only care the gate passed.
        with patch(
            "app.services.ai_client.call_ai", return_value='["Docker", "Kubernetes"]'
        ):
            async with await _client_as(pro_user, db_session) as ac:
                r = await ac.post("/api/v1/resume/suggest-skills", json=_SUGGEST_PAYLOAD)
        app.dependency_overrides.clear()

        assert r.status_code == 200

    async def test_pro_user_passes_cover_letter_gate(
        self, db_session: AsyncSession
    ):
        pro_user = _make_user("pro")
        with patch(
            "app.services.ai_client.call_ai", return_value="Dear hiring team,\n\n..."
        ):
            async with await _client_as(pro_user, db_session) as ac:
                r = await ac.post("/api/v1/resume/cover-letter", json=_COVER_LETTER_PAYLOAD)
        app.dependency_overrides.clear()

        assert r.status_code == 200


class TestPlanGatingEnterpriseInheritsPro:
    async def test_enterprise_user_passes_pro_gate(
        self, db_session: AsyncSession
    ):
        ent_user = _make_user("enterprise")
        with patch(
            "app.services.ai_client.call_ai", return_value='["Terraform"]'
        ):
            async with await _client_as(ent_user, db_session) as ac:
                r = await ac.post("/api/v1/resume/suggest-skills", json=_SUGGEST_PAYLOAD)
        app.dependency_overrides.clear()

        assert r.status_code == 200
