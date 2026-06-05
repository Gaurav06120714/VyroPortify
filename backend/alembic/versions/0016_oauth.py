"""OAuth 2.0 tables — apps, codes, access tokens (v3.0.2).

Revision ID: 0016_oauth
Revises: 0015_webhooks
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "0016_oauth"
down_revision: str | None = "0015_webhooks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_TS_COLS = [
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
]


def upgrade() -> None:
    op.create_table(
        "oauth_apps",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_user_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("client_secret_hash", sa.String(64), nullable=False),
        sa.Column("redirect_uris", sa.Text, nullable=False, server_default=""),
        sa.Column("homepage_url", sa.Text, nullable=True),
        *_TS_COLS,
    )
    op.create_index("ix_oauth_apps_owner_user_id", "oauth_apps", ["owner_user_id"])
    op.create_index("ix_oauth_apps_client_id", "oauth_apps", ["client_id"], unique=True)

    op.create_table(
        "oauth_authorization_codes",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("app_id", PG_UUID(as_uuid=True), sa.ForeignKey("oauth_apps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("redirect_uri", sa.Text, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False, server_default=""),
        sa.Column("code_challenge", sa.String(128), nullable=True),
        sa.Column("code_challenge_method", sa.String(8), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *_TS_COLS,
    )
    op.create_index("ix_oauth_authorization_codes_code_hash", "oauth_authorization_codes", ["code_hash"], unique=True)
    op.create_index("ix_oauth_authorization_codes_app_id", "oauth_authorization_codes", ["app_id"])
    op.create_index("ix_oauth_authorization_codes_user_id", "oauth_authorization_codes", ["user_id"])

    op.create_table(
        "oauth_access_tokens",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("app_id", PG_UUID(as_uuid=True), sa.ForeignKey("oauth_apps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("scopes", sa.Text, nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *_TS_COLS,
    )
    op.create_index("ix_oauth_access_tokens_token_hash", "oauth_access_tokens", ["token_hash"], unique=True)
    op.create_index("ix_oauth_access_tokens_app_id", "oauth_access_tokens", ["app_id"])
    op.create_index("ix_oauth_access_tokens_user_id", "oauth_access_tokens", ["user_id"])


def downgrade() -> None:
    for tbl in ("oauth_access_tokens", "oauth_authorization_codes", "oauth_apps"):
        op.drop_table(tbl)
