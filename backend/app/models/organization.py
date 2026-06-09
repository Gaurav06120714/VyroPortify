"""Organization + Membership models (v2.0.0).

The data model shift from a single-user product to a multi-tenant one is
opt-in for existing users: every legacy account is backfilled into a
single-member personal organization (v2.0.5) so the API contract stays
identical for users who don't invite anyone.

Why a separate Membership table instead of a roles array on User?
  - One user can belong to many orgs (consultant joining a client org).
  - Role lives on the edge (user × org), not the node. Updating a user's
    role in org A must not touch org B.
  - The unique (organization_id, user_id) constraint enforces "exactly
    one membership per pair" at the DB level — no app-level dedupe.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A workspace that owns portfolios + resumes + billing."""

    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_slug", "slug", unique=True),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    
    slug: Mapped[str] = mapped_column(String(120), nullable=False)

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="free",
        comment="free | pro | enterprise",
    )

    is_personal: Mapped[bool] = mapped_column(
        nullable=False, server_default="false"
    )

    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    font_family: Mapped[str | None] = mapped_column(String(120), nullable=True)
    
    custom_css: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    hide_branding: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User ↔ Organization edge with a role."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="uq_memberships_org_user"
        ),
        Index("ix_memberships_user_id", "user_id"),
        Index("ix_memberships_organization_id", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="owner",
        comment="owner | admin | editor | viewer",
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships"
    )
    user: Mapped["User"] = relationship()
