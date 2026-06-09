import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.user import User

class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Uploaded resume document with parsed content."""

    __tablename__ = "resumes"
    __table_args__ = (
        Index("ix_resumes_user_id", "user_id"),
        
        Index("ix_resumes_status", "status"),
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
    
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="pdf | docx"
    )
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Structured JSON extracted from the resume"
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="pending",
        comment="pending | processing | done | failed",
    )

    user: Mapped["User"] = relationship(back_populates="resumes")
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} user_id={self.user_id} status={self.status!r}>"
