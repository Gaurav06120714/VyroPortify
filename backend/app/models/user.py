from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ai_job import AIJob
    from app.models.portfolio import Portfolio
    from app.models.resume import Resume


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Application user — auth handled by Clerk (clerk_user_id is the primary lookup key)."""

    __tablename__ = "users"

    # Clerk user ID — e.g. "user_2abc..."  Used for JWT → User resolution.
    clerk_user_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    # hashed_password kept as nullable so existing rows don't break; not used with Clerk.
    hashed_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="free",
        comment="free | pro | enterprise",
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    # v2.1.1 — Stripe Connect Express account for template authors.
    # NULL means the user hasn't onboarded as a seller yet.
    stripe_account_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_jobs: Mapped[list["AIJob"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} clerk_user_id={self.clerk_user_id!r} email={self.email!r}>"
