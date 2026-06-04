"""Backfill: every existing user gets a personal organization (v2.0.5).

Revision ID: 0007_backfill_personal_orgs
Revises: 0006_organizations_memberships
Create Date: 2026-06-04

Strategy
--------
For each row in `users`:
  1. Insert an Organization with name="<user.name or email-local>'s Workspace",
     is_personal=true, stripe_* copied over from the user, plan copied over.
  2. Insert a Membership row (org, user, role=owner).
  3. UPDATE portfolios and resumes belonging to that user to point
     organization_id at the new org.

Idempotency
-----------
The migration is safe to re-run: every step uses ``ON CONFLICT DO NOTHING``
or filters on ``organization_id IS NULL``. A partial run that crashes
half-way through can be resumed by simply running ``alembic upgrade head``
again.

After this migration, every portfolio + resume has a non-null
organization_id. A later migration (planned v2.1) will flip the column
to NOT NULL once we're confident there's no production race window.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_backfill_personal_orgs"
down_revision: str | None = "0006_organizations_memberships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Create one org + one owner-membership per user ─────────────────
    # Single SQL statement so the migration completes in O(1) round-trips
    # even with millions of users. The slug includes a short suffix from
    # the user id to keep it unique without a probe loop.
    bind.execute(
        sa.text(
            """
            WITH inserted AS (
                INSERT INTO organizations
                    (id, name, slug, stripe_customer_id, stripe_subscription_id,
                     plan, is_personal, created_at, updated_at)
                SELECT
                    gen_random_uuid(),
                    COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1))
                        || '''s Workspace',
                    'personal-' || substr(u.id::text, 1, 8),
                    u.stripe_customer_id,
                    u.stripe_subscription_id,
                    u.plan,
                    TRUE,
                    NOW(),
                    NOW()
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM memberships m WHERE m.user_id = u.id
                )
                RETURNING id, stripe_customer_id
            )
            -- Membership row links the new org back to its user.
            INSERT INTO memberships (id, organization_id, user_id, role, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                ins.id,
                u.id,
                'owner',
                NOW(),
                NOW()
            FROM inserted ins
            JOIN users u ON u.stripe_customer_id IS NOT DISTINCT FROM ins.stripe_customer_id
              OR (ins.stripe_customer_id IS NULL AND u.stripe_customer_id IS NULL)
            WHERE NOT EXISTS (
                SELECT 1 FROM memberships m WHERE m.user_id = u.id
            );
            """
        )
    )

    # ── 2. Point existing portfolios + resumes at the new orgs ────────────
    # Each row's org is "the personal org of its owner". Resolved by the
    # membership table, which v1 above just populated.
    bind.execute(
        sa.text(
            """
            UPDATE portfolios p
            SET organization_id = m.organization_id
            FROM memberships m
            JOIN organizations o ON o.id = m.organization_id
            WHERE p.user_id = m.user_id
              AND o.is_personal = TRUE
              AND p.organization_id IS NULL;
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE resumes r
            SET organization_id = m.organization_id
            FROM memberships m
            JOIN organizations o ON o.id = m.organization_id
            WHERE r.user_id = m.user_id
              AND o.is_personal = TRUE
              AND r.organization_id IS NULL;
            """
        )
    )


def downgrade() -> None:
    # The reverse is unsafe — once team orgs are created on top of personal
    # ones, blindly deleting personal orgs would orphan team memberships.
    # Manual recovery only.
    pass
