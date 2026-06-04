"""Unit tests for app.core.authz."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.authz import assert_owner, require_plan
from app.core.enums import Plan
from app.core.exceptions import PlanLimitExceeded


def _user(id_: str) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.UUID(id_))


def _resource(owner_id: str) -> SimpleNamespace:
    return SimpleNamespace(user_id=uuid.UUID(owner_id))


class TestAssertOwner:
    def test_returns_resource_when_owned_by_user(self):
        user = _user("00000000-0000-0000-0000-000000000001")
        resource = _resource("00000000-0000-0000-0000-000000000001")

        assert assert_owner(resource, user) is resource

    def test_raises_404_when_resource_is_none(self):
        user = _user("00000000-0000-0000-0000-000000000001")

        with pytest.raises(HTTPException) as exc:
            assert_owner(None, user)
        assert exc.value.status_code == 404

    def test_raises_404_when_owned_by_someone_else(self):
        user = _user("00000000-0000-0000-0000-000000000001")
        resource = _resource("00000000-0000-0000-0000-000000000002")

        with pytest.raises(HTTPException) as exc:
            assert_owner(resource, user)
        # Must be 404, never 403 — 403 would leak resource existence.
        assert exc.value.status_code == 404


def _principal(plan: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.UUID("00000000-0000-0000-0000-000000000010"), plan=plan
    )


class TestRequirePlan:
    def test_free_user_blocked_from_pro_feature(self):
        dep = require_plan(Plan.PRO, feature="AI cover letter")
        with pytest.raises(PlanLimitExceeded) as exc:
            dep(_principal("free"))
        assert "Pro" in exc.value.message
        assert "AI cover letter" in exc.value.message

    def test_pro_user_passes_pro_gate(self):
        dep = require_plan(Plan.PRO)
        user = _principal("pro")
        assert dep(user) is user

    def test_enterprise_user_passes_pro_gate(self):
        dep = require_plan(Plan.PRO)
        user = _principal("enterprise")
        assert dep(user) is user

    def test_unknown_plan_value_treated_as_free(self):
        # Defensive: a malformed plan column must not silently grant access.
        dep = require_plan(Plan.PRO)
        with pytest.raises(PlanLimitExceeded):
            dep(_principal("garbage"))
