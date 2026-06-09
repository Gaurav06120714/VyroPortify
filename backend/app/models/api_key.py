"""Personal API keys for the public REST API (v3.0.0).

Keys are issued as `vp_<32 random url-safe chars>`. We store only:
  - prefix (first 8 chars after `vp_`) for display + lookup hint
  - sha256(key) so the raw key cannot be recovered if the DB is compromised

Scopes are a comma-separated whitelist (e.g. "portfolios:read,resumes:read").
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

class APIKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()

    def scope_list(self) -> list[str]:
        return [s for s in (self.scopes or "").split(",") if s]

    def is_active(self, now: datetime) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= now:
            return False
        return True
