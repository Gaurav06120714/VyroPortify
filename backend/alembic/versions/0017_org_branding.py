"""Organization white-label branding columns (v3.0.3).

Revision ID: 0017_org_branding
Revises: 0016_oauth
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_org_branding"
down_revision: str | None = "0016_oauth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("logo_url", sa.Text, nullable=True))
    op.add_column("organizations", sa.Column("primary_color", sa.String(9), nullable=True))
    op.add_column("organizations", sa.Column("accent_color", sa.String(9), nullable=True))
    op.add_column("organizations", sa.Column("font_family", sa.String(120), nullable=True))
    op.add_column("organizations", sa.Column("custom_css", sa.Text, nullable=True))
    op.add_column(
        "organizations",
        sa.Column("hide_branding", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    for col in ("hide_branding", "custom_css", "font_family", "accent_color", "primary_color", "logo_url"):
        op.drop_column("organizations", col)
