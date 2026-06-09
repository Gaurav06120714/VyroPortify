import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.template import Template
    from app.models.user import User

class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generated portfolio site derived from a user's resume."""

    __tablename__ = "portfolios"
    __table_args__ = (
        Index("ix_portfolios_user_id", "user_id"),
        
        Index("ix_portfolios_slug", "slug", unique=True),
        
        Index("ix_portfolios_is_public", "is_public"),
        
        Index("ix_portfolios_status", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    template_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Rendered section content keyed by section name"
    )
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(253), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    views: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="draft",
        comment="draft | published | archived",
    )

    user: Mapped["User"] = relationship(back_populates="portfolios")
    resume: Mapped["Resume | None"] = relationship(back_populates="portfolios")
    template: Mapped["Template | None"] = relationship(back_populates="portfolios")

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} slug={self.slug!r} status={self.status!r}>"
