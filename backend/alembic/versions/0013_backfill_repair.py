"""Repair any state left by the broken v1 of 0007_backfill_personal_orgs.

Revision ID: 0013_backfill_repair
Revises: 0012_resume_exports
Create Date: 2026-06-05

The original 0007 joined newly-inserted personal Organizations back
to Users via `stripe_customer_id`. For users with NULL customer id
(every free user) that produced cartesian rows — either exploding
into duplicate memberships or, more commonly, blowing up the
uq_memberships_org_user constraint and leaving an incomplete state
(orphaned personal Orgs, some Users with no Membership at all).

This migration is **forward-only and idempotent**:

  1. Delete orphan personal Organizations — is_personal=TRUE rows
     that have zero Memberships.
  2. For any User without a Membership, create one fresh personal
     Org + owner Membership (the corrected logic from the new 0007).
  3. Re-run the portfolio/resume organization_id backfill so
     anything orphaned by step 1 picks up its owner's org.

Safe on a clean DB (every step is a no-op when there's nothing to
fix). Re-runnable.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_backfill_repair"
down_revision: str | None = "0012_resume_exports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Drop orphan personal orgs (no member).
    bind.execute(
        sa.text(
            """
            DELETE FROM organizations o
            WHERE o.is_personal = TRUE
              AND NOT EXISTS (
                  SELECT 1 FROM memberships m WHERE m.organization_id = o.id
              );
            """
        )
    )

    # 2. Backfill personal org + owner Membership for any User without one.
    #    Same corrected CTE shape as the rewritten 0007.
    bind.execute(
        sa.text(
            """
            WITH source AS (
                SELECT
                    gen_random_uuid()                                   AS org_id,
                    u.id                                                AS user_id,
                    COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1))
                        || '''s Workspace'                              AS name,
                    'personal-' || substr(u.id::text, 1, 8)             AS slug,
                    u.stripe_customer_id                                AS stripe_customer_id,
                    u.stripe_subscription_id                            AS stripe_subscription_id,
                    u.plan                                              AS plan
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM memberships m WHERE m.user_id = u.id
                )
            ),
            inserted_orgs AS (
                INSERT INTO organizations
                    (id, name, slug, stripe_customer_id, stripe_subscription_id,
                     plan, is_personal, created_at, updated_at)
                SELECT org_id, name, slug, stripe_customer_id,
                       stripe_subscription_id, plan, TRUE, NOW(), NOW()
                FROM source
                RETURNING id
            )
            INSERT INTO memberships
                (id, organization_id, user_id, role, created_at, updated_at)
            SELECT gen_random_uuid(), s.org_id, s.user_id, 'owner', NOW(), NOW()
            FROM source s
            JOIN inserted_orgs i ON i.id = s.org_id;
            """
        )
    )

    # 3. Re-do the portfolio/resume backfill in case the original
    #    UPDATE picked an orphan org id (since deleted in step 1).
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
    # No-op — undoing a repair would re-introduce the broken state.
    pass
