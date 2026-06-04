"""Authorization primitives.

Centralized ownership / access checks. Every route that fetches a user-scoped
resource by ID must enforce ownership before returning it. Using a single
helper makes this audit-friendly and gives a single seam to extend later
(team/org scoping in v2.0).

Convention: when a resource is not owned by the caller we raise 404, not 403.
A 403 leaks resource existence ("this ID exists, you just can't see it"); 404
is indistinguishable from "no such resource" and is the OWASP-recommended
response for authorization failures on direct-object references.
"""

from __future__ import annotations

import uuid
from typing import Callable, Protocol, TypeVar

from fastapi import Depends, HTTPException, status

from app.core.enums import Plan
from app.core.exceptions import PlanLimitExceeded
from app.models.user import User
from app.security import CurrentUser


class _OwnedResource(Protocol):
    user_id: uuid.UUID


class _Principal(Protocol):
    id: uuid.UUID


T = TypeVar("T", bound=_OwnedResource)


def assert_owner(resource: T | None, user: _Principal) -> T:
    """Return *resource* if it exists and is owned by *user*, else raise 404.

    Single source of truth for owner-based authorization. Call sites must use
    this rather than re-implementing the `user_id == current_user.id` check
    inline, so that the policy can evolve in one place (e.g. team membership
    in v2.0).
    """
    if resource is None or resource.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    return resource


# ── Plan gating ────────────────────────────────────────────────────────────────

# Plans are ordered so that a higher plan satisfies any lower-plan requirement.
_PLAN_RANK: dict[Plan, int] = {
    Plan.FREE: 0,
    Plan.PRO: 1,
    Plan.ENTERPRISE: 2,
}


def require_plan(minimum: Plan, *, feature: str | None = None) -> Callable[[User], User]:
    """FastAPI dependency that enforces a minimum plan for the current user.

    Usage:
        @router.post("/cover-letter", dependencies=[Depends(require_plan(Plan.PRO))])

    Raises PlanLimitExceeded (HTTP 403, error_code PLAN_LIMIT_EXCEEDED) when the
    caller is below the required tier. The global PortifyBaseException handler
    converts this to a structured JSON response with a correlation id.
    """

    minimum_rank = _PLAN_RANK[minimum]
    label = feature or "this feature"

    def _dependency(current_user: CurrentUser) -> User:
        try:
            user_plan = Plan(current_user.plan)
        except ValueError:
            user_plan = Plan.FREE

        if _PLAN_RANK[user_plan] < minimum_rank:
            raise PlanLimitExceeded(
                f"{label} requires the {minimum.value.title()} plan. "
                f"Upgrade to continue."
            )
        return current_user

    return _dependency


# ── Role-based access (v2.0.1) ────────────────────────────────────────────────

# Roles are ordered so a higher role satisfies any lower-role requirement.
_ROLE_RANK: dict[str, int] = {
    "viewer": 0,
    "editor": 1,
    "admin": 2,
    "owner": 3,
}


def has_role(role: str, minimum: str) -> bool:
    """Pure helper for unit tests and service code."""
    return _ROLE_RANK.get(role, -1) >= _ROLE_RANK[minimum]


def require_role(minimum: str) -> Callable:
    """FastAPI dependency: caller must hold *minimum* role in the org named in
    the path parameter ``org_id``.

    Implementation note: we resolve the membership inside the dependency so
    every route sharing the same dependency gets the same answer. We import
    the database session and Membership lazily to keep the authz module
    free of circular imports.
    """

    from uuid import UUID
    from fastapi import HTTPException, Request, status as http_status

    async def _dependency(
        request: Request, current_user: CurrentUser
    ) -> "Membership":
        # Late imports — keep core.authz lightweight at module load.
        from sqlalchemy import select

        from app.database import get_db
        from app.models.organization import Membership

        raw_org = request.path_params.get("org_id")
        if raw_org is None:
            # Programmer error: applied to a route without /:org_id/. Surface
            # loudly so we catch it in tests rather than silently accepting.
            raise RuntimeError(
                "require_role applied to a route without an {org_id} path param"
            )
        try:
            org_id = UUID(str(raw_org))
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Pull the same session FastAPI gives downstream handlers. We don't
        # want a second connection just for the role check.
        async for db in get_db():
            result = await db.execute(
                select(Membership).where(
                    Membership.organization_id == org_id,
                    Membership.user_id == current_user.id,
                )
            )
            membership = result.scalar_one_or_none()
            break

        if membership is None or not has_role(membership.role, minimum):
            # Same 404 (not 403) policy as assert_owner — never leak the
            # existence of an org the caller can't see.
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return membership

    return _dependency
