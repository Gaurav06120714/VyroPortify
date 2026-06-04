"""Unit tests for app.core.authz.assert_owner."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.authz import assert_owner


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
