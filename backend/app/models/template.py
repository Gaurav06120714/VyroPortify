import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio

class Template(TimestampMixin, Base):
    """Portfolio visual template.

    v2.1.0 — Marketplace fields added on top of the original
    admin-managed catalog. Built-in templates have author_user_id=NULL
    and status='approved'; community submissions start at 'pending'
    until a moderator (org owner) approves them.
    """

    __tablename__ = "templates"
    __table_args__ = (
        Index("ix_templates_status", "status"),
        Index("ix_templates_author", "author_user_id"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="personal | developer | designer | executive",
    )
    is_pro: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    config: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
        comment="Layout, color scheme, font, and section-visibility settings",
    )

    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="approved",
        comment="draft | pending | approved | rejected",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
        comment="0 for free; >0 for paid templates (USD cents)",
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    downloads_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )
    rating_average: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )

    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="template")

    def __repr__(self) -> str:
        return f"<Template id={self.id!r} name={self.name!r} status={self.status!r}>"

class TemplateReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One review per (template, user). The unique constraint enforces that
    a user can't pad ratings; updates use upsert semantics in the service."""

    __tablename__ = "template_reviews"
    __table_args__ = (
        UniqueConstraint(
            "template_id", "user_id", name="uq_template_reviews_template_user"
        ),
        CheckConstraint(
            "rating BETWEEN 1 AND 5", name="ck_template_reviews_rating_range"
        ),
        Index("ix_template_reviews_template", "template_id"),
    )

    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
