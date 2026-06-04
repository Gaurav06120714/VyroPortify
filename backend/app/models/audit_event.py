"""AuditEvent — queryable audit trail (v2.0.2).

The existing app.core.audit_log emits structured log lines for SIEM ingest.
This table is the *user-visible* trail: shown in the Settings → Audit Log
page so org admins can see who did what in their workspace.

Two different surfaces, two different storages, on purpose:
  - log_security_event() → stdout / Datadog. High-volume, security ops.
  - record_audit()       → this table. Low-volume, user-facing.

Schema is intentionally generic (action + target_type + target_id +
meta JSONB) so adding a new auditable event later only needs a new
record_audit() call, no migration.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_org_created", "organization_id", "created_at"),
        Index("ix_audit_events_action", "action"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # e.g. "portfolio.publish", "membership.invite", "billing.upgrade"
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Arbitrary structured context. Must never contain PII or secrets —
    # callers are responsible for redaction at the source.
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
