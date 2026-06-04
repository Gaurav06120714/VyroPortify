"""Add a case-insensitive unique index on portfolios.custom_domain.

Revision ID: 0005_unique_custom_domain
Revises: 0004_add_performance_indexes
Create Date: 2026-06-04

custom_domain was added in the initial schema but without a uniqueness
constraint, so two users could (in principle) claim the same domain. We
add a partial unique index keyed on lower(custom_domain), which both
deduplicates and serves the public-lookup query path
(`WHERE lower(custom_domain) = lower($1)`).

The index is partial — it skips NULL rows so the bulk of portfolios
(no custom domain) don't pay any cost.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_unique_custom_domain"
down_revision: str | None = "0004_add_performance_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_portfolios_custom_domain_lower "
        "ON portfolios (lower(custom_domain)) "
        "WHERE custom_domain IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_portfolios_custom_domain_lower")
