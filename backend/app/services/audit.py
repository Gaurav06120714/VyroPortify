"""record_audit — write a user-visible audit event (v2.0.2).

Two ergonomic helpers so call sites don't have to import the model:
  - record_audit(db, org_id, actor, action, ...) -> AuditEvent
  - record_audit_safe(...) — same, but swallows exceptions so a logging
    failure can never break a billing/portfolio mutation.

The DB session is expected to be the caller's request session — we do
NOT open a new connection. That way the audit row commits/rolls back
atomically with the action that produced it.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


async def record_audit(
    db: Any,
    *,
    organization_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        meta=meta,
    )
    db.add(event)
    await db.flush()
    return event


async def record_audit_safe(db: Any, **kwargs: Any) -> None:
    try:
        await record_audit(db, **kwargs)
    except Exception as exc:  # noqa: BLE001 — intentional broad catch
        logger.warning("record_audit_failed: %s", exc)
