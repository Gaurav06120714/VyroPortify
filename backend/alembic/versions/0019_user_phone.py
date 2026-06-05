"""Add users.phone_number (v3.4.0).

Revision ID: 0019_user_phone
Revises: 0018_sso_configs
Create Date: 2026-06-06

Phone number is captured by Clerk during signup (verified via SMS OTP) and
mirrored here via the Clerk webhook. Nullable because pre-Clerk-phone users
remain valid; UNIQUE when present so a single mobile can't sign up twice.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_user_phone"
down_revision: str | None = "0018_sso_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(32), nullable=True))
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_column("users", "phone_number")
