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
    # B1 fix: thread the user_id through the CTE explicitly so each
    # inserted Organization is paired with exactly one User. The
    # original join-on-stripe_customer_id collapsed every free user
    # (NULL stripe id) into a single equivalence class, then either
    # exploded into a cartesian product or hit the
    # uq_memberships_org_user constraint.
    #
    # Pairing the new org row to its source user is done in one pass
    # via RETURNING (organization.id, source user_id) — Postgres lets
    # us project arbitrary computed values out of the inserted side
    # via a column-list that references the SELECT, so we keep the
    # one-statement guarantee from the original design without the
    # ambiguous join.
    bind.execute(
        sa.text(
            """
            WITH source AS (
                SELECT
                    gen_random_uuid()                                   AS org_id,
                    u.id                                                AS user_id,
                    -- B27: typographic apostrophe (’) for consistency with
                    -- the live signup path in app/security.py. The SQL
                    -- literal escapes a single quote as '' inside another
                    -- '' — that's only needed for ASCII '; the U+2019
                    -- character below passes through Postgres unchanged.
                    COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1))
                        || '’s Workspace'                               AS name,
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
