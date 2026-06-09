"""OAuth 2.0 (authorization-code + PKCE) models (v3.0.2)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

class OAuthApp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registered third-party application that requests access on behalf of a user."""

    __tablename__ = "oauth_apps"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    client_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    client_secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    redirect_uris: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    homepage_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship()

    def redirect_uri_list(self) -> list[str]:
        return [u for u in (self.redirect_uris or "").split(",") if u]

class OAuthAuthorizationCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Short-lived authorization code issued at /oauth/authorize."""

    __tablename__ = "oauth_authorization_codes"

    app_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("oauth_apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    code_challenge: Mapped[str | None] = mapped_column(String(128), nullable=True)
    code_challenge_method: Mapped[str | None] = mapped_column(String(8), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class OAuthAccessToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Bearer token returned from /oauth/token in exchange for an authorization code."""

    __tablename__ = "oauth_access_tokens"

    app_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("oauth_apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def scope_list(self) -> list[str]:
        return [s for s in (self.scopes or "").split(",") if s]

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now
