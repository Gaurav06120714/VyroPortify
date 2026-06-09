"""PortfolioView — append-only analytics event (v2.0.3).

One row per public-portfolio page load. Aggregated server-side into the
shape the dashboard wants. We don't store the full IP/UA — keep it
privacy-conscious by hashing the IP+UA into an opaque session token so
"unique visitors" is countable but the visitor isn't identifiable.

Lower-cost alternatives like a Redis counter give totals but lose the
per-day / per-country breakdown the analytics page surfaces, so the row
overhead is worth it.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

class PortfolioView(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_views"
    __table_args__ = (
        Index("ix_portfolio_views_portfolio_created", "portfolio_id", "created_at"),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    session_token: Mapped[str] = mapped_column(String(64), nullable=False)
    referrer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
