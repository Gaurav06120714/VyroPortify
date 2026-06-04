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
