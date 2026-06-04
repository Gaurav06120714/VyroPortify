"""Extend templates with marketplace fields + create template_reviews.

Revision ID: 0010_template_marketplace
Revises: 0009_portfolio_views
Create Date: 2026-06-04

v2.1.0 — Community submission + moderation.

Templates have been an admin-managed catalog up to now. We extend the
existing row with marketplace metadata (author, status, pricing,
download counts, rating cache) and add a separate template_reviews
table for the per-user 1-5 ratings. The rating cache columns
(rating_average, rating_count) on templates are refreshed by a
service helper after each review insert so list/sort by rating is
cheap.

All new columns are nullable / have server defaults, so existing
built-in templates (aurora, minimal, cyber, executive) keep working
unchanged: author_user_id NULL means "built-in", status defaults to
"approved" so the existing catalog stays visible.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_template_marketplace"
down_revision: str | None = "0009_portfolio_views"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── extend templates ──────────────────────────────────────────────────
    op.add_column(
        "templates",
        sa.Column(
            "author_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "templates",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="approved",
            comment="draft | pending | approved | rejected",
        ),
    )
    op.add_column(
        "templates",
        sa.Column(
            "description", sa.Text(), nullable=True,
        ),
    )
    op.add_column(
        "templates",
        sa.Column(
            "price_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0 for free; >0 for paid templates (USD cents)",
        ),
    )
    op.add_column(
        "templates",
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "templates",
        sa.Column(
            "downloads_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "templates",
        sa.Column(
            "rating_average",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "templates",
        sa.Column(
            "rating_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        "ix_templates_status", "templates", ["status"], if_not_exists=True
    )
    op.create_index(
        "ix_templates_author", "templates", ["author_user_id"], if_not_exists=True
    )

    # ── template_reviews ──────────────────────────────────────────────────
    op.create_table(
        "template_reviews",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            sa.String(100),
            sa.ForeignKey("templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
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
        # One review per (template, user) — updates replace, no duplicates.
        sa.UniqueConstraint(
            "template_id", "user_id", name="uq_template_reviews_template_user"
        ),
        # Rating must be 1..5; enforced at the DB level so a bad client
        # can't poison the rating cache.
        sa.CheckConstraint(
            "rating BETWEEN 1 AND 5", name="ck_template_reviews_rating_range"
        ),
    )
    op.create_index(
        "ix_template_reviews_template",
        "template_reviews",
        ["template_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_template_reviews_template", table_name="template_reviews")
    op.drop_table("template_reviews")
    op.drop_index("ix_templates_author", table_name="templates")
    op.drop_index("ix_templates_status", table_name="templates")
    for col in (
        "rating_count",
        "rating_average",
        "downloads_count",
        "stripe_price_id",
        "price_cents",
        "description",
        "status",
        "author_user_id",
    ):
        op.drop_column("templates", col)
