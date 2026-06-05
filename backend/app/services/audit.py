"""record_audit — write a user-visible audit event (v2.0.2).

Two ergonomic helpers so call sites don't have to import the model:
  - record_audit(db, org_id, actor, action, ...) -> AuditEvent
  - record_audit_safe(...) — same, but swallows exceptions so a logging
    failure can never break a billing/portfolio mutation.

Commit semantics (B14)
----------------------
Both helpers operate on the *caller's* DB session and emit a flush()
only — they do NOT commit. The caller decides whether the audit row
commits alongside their mutation (which is the normal case) or is
discarded as part of a rollback. The "_safe" suffix refers to
exception swallowing, not auto-commit; the docstring used to be
ambiguous on that and a few call sites assumed the helper would
persist on its own. The behavior is unchanged; only the docs and
the call-site invariant are tightened.
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
    """Stage an AuditEvent for commit by the caller.

    Flushes to obtain the row id, but does NOT commit. Caller must
    `await db.commit()` after their own work for the event to persist.
    """
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
    """Stage an AuditEvent, swallowing any exception.

    "Safe" = exception-safe, not auto-commit. The audit row is staged
    on *db* alongside the caller's other writes; both persist when the
    caller commits, both roll back if the caller doesn't. If the
    staging itself fails (e.g. the AuditEvent row violates a
    constraint we didn't anticipate), we log + drop instead of letting
    the audit pipeline take down the user-facing mutation that
    triggered it.
    """
    try:
        await record_audit(db, **kwargs)
    except Exception as exc:  # noqa: BLE001 — intentional broad catch
        logger.warning("record_audit_failed: %s", exc)
