"""ResumeExport — generated PDF artifacts (v2.3).

Each row records one (resume × template) PDF render. We key on the
content_hash of the source payload so identical re-exports hit a
cache (a returning `Download PDF` click on unchanged data returns the
same s3_key rather than recompiling).
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ResumeExport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_exports"
    __table_args__ = (
        # Quick lookup by (resume, content) — used by the cache check on
        # repeated download attempts.
        Index("ix_resume_exports_resume_hash", "resume_id", "content_hash"),
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # SHA-256 of (template_id + serialized resume payload). Same input →
    # same row → cache hit.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    template_id: Mapped[str] = mapped_column(String(40), nullable=False)
    # S3/R2 object key. The presigned URL is generated on demand so the
    # row never holds a time-limited link.
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Which engine actually rendered this row — useful for telemetry +
    # debugging "why does my PDF look different today?" reports.
    engine: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="tectonic | reportlab",
    )
