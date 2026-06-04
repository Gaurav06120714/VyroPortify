"""Add users.stripe_account_id for Stripe Connect (v2.1.1).

Revision ID: 0011_user_stripe_account
Revises: 0010_template_marketplace
Create Date: 2026-06-04

Connected-account id from Stripe Express onboarding. Nullable because
only users who choose to sell paid templates ever onboard.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_user_stripe_account"
down_revision: str | None = "0010_template_marketplace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("stripe_account_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_users_stripe_account_id",
        "users",
        ["stripe_account_id"],
        unique=True,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_stripe_account_id", table_name="users")
    op.drop_column("users", "stripe_account_id")
