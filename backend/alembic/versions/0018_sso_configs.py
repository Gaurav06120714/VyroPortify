"""SSO/SAML configuration per org (v3.0.5).

Revision ID: 0018_sso_configs
Revises: 0017_org_branding
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "0018_sso_configs"
down_revision: str | None = "0017_org_branding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sso_configs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idp_entity_id", sa.String(255), nullable=False),
        sa.Column("idp_sso_url", sa.Text, nullable=False),
        sa.Column("idp_x509_cert", sa.Text, nullable=False),
        sa.Column("sp_entity_id", sa.String(255), nullable=False),
        sa.Column("email_domain", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sso_configs_organization_id", "sso_configs", ["organization_id"], unique=True)
    op.create_index("ix_sso_configs_email_domain", "sso_configs", ["email_domain"])


def downgrade() -> None:
    op.drop_table("sso_configs")
