"""Create portfolio_views table (v2.0.3)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_portfolio_views"
down_revision: str | None = "0008_audit_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolio_views",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("portfolios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_token", sa.String(64), nullable=False),
        sa.Column("referrer", sa.String(255), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_portfolio_views_portfolio_created",
        "portfolio_views",
        ["portfolio_id", "created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_portfolio_views_portfolio_created", table_name="portfolio_views"
    )
    op.drop_table("portfolio_views")
