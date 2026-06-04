"""Create resume_exports table (v2.3)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_resume_exports"
down_revision: str | None = "0011_user_stripe_account"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_exports",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resume_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("template_id", sa.String(40), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("engine", sa.String(20), nullable=True),
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
        "ix_resume_exports_resume_hash",
        "resume_exports",
        ["resume_id", "content_hash"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_resume_exports_resume_hash", table_name="resume_exports")
    op.drop_table("resume_exports")
