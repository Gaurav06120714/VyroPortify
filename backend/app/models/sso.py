"""Per-organization SSO/SAML configuration (v3.0.5)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class SSOConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """SAML 2.0 SP configuration per organization. One row per org."""

    __tablename__ = "sso_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # IdP metadata
    idp_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idp_sso_url: Mapped[str] = mapped_column(Text, nullable=False)
    idp_x509_cert: Mapped[str] = mapped_column(Text, nullable=False)
    # SP-side
    sp_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # Email domain that must be claimed in SAML NameID — gates which users this org owns
    email_domain: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    organization: Mapped["Organization"] = relationship()
