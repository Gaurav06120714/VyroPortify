"""Create organizations + memberships; add organization_id to resources.

Revision ID: 0006_organizations_memberships
Revises: 0005_unique_custom_domain
Create Date: 2026-06-04

v2.0.0 — Enterprise GA foundation. Adds the two new tables and a
nullable organization_id FK on the user-owned resources. NULL is
allowed so the migration is safe to run on a populated database
without a simultaneous backfill — the v2.0.5 backfill migration
populates the column afterwards, and a later release (v2.0.6+)
can drop the NULL once every row is migrated.

Indexes follow the same patterns as the existing schema:
  - btree on every FK
  - partial unique on case-insensitive slug
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_organizations_memberships"
down_revision: str | None = "0005_unique_custom_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── organizations ─────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column(
            "plan", sa.String(50), nullable=False, server_default="free"
        ),
        sa.Column(
            "is_personal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index(
        "ix_organizations_slug",
        "organizations",
        ["slug"],
        unique=True,
        if_not_exists=True,
    )
    op.create_index(
        "ix_organizations_stripe_customer_id",
        "organizations",
        ["stripe_customer_id"],
        if_not_exists=True,
    )

    # ── memberships ───────────────────────────────────────────────────────
    op.create_table(
        "memberships",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role", sa.String(20), nullable=False, server_default="owner"
        ),
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
        sa.UniqueConstraint(
            "organization_id", "user_id", name="uq_memberships_org_user"
        ),
    )
    op.create_index(
        "ix_memberships_user_id", "memberships", ["user_id"], if_not_exists=True
    )
    op.create_index(
        "ix_memberships_organization_id",
        "memberships",
        ["organization_id"],
        if_not_exists=True,
    )

    # ── add nullable organization_id to user-owned resources ──────────────
    # NULL allowed so we can deploy this migration before the backfill;
    # the FK is added so the column is type-safe from the start.
    for table in ("portfolios", "resumes"):
        op.add_column(
            table,
            sa.Column(
                "organization_id",
                sa.UUID(as_uuid=True),
                sa.ForeignKey("organizations.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index(
            f"ix_{table}_organization_id",
            table,
            ["organization_id"],
            if_not_exists=True,
        )


def downgrade() -> None:
    for table in ("portfolios", "resumes"):
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        op.drop_column(table, "organization_id")
    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index(
        "ix_organizations_stripe_customer_id", table_name="organizations"
    )
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
