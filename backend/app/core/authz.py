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
from typing import Protocol, TypeVar

from fastapi import HTTPException, status


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
