"""Seed the four canonical built-in templates.

Revision ID: 0013_seed_builtin_templates
Revises: 0012_resume_exports
Create Date: 2026-06-05

A fresh DB used to come up with an empty `templates` table, which made
POST /portfolio/generate 5xx with a foreign-key violation the moment a
user clicked "Build my portfolio" (the column `portfolios.template_id`
references `templates.id`, and the frontend always asks for `aurora`).

Idempotent INSERT … ON CONFLICT DO NOTHING so the migration is safe to
re-run and so a custom-edited templates row in production isn't
overwritten. Marketplace community templates (status='pending') are a
separate code path that coexists with these built-ins.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_seed_builtin_templates"
down_revision: str | None = "0012_resume_exports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Mirrors scripts/seed_templates.py — keep in sync. Inline so the
# migration has zero import dependency on the application code.
_TEMPLATES: list[tuple[str, str, str, str, bool]] = [
    ("aurora",    "Aurora",    "developer", "https://cdn.vyroportify.com/previews/aurora.png",    False),
    ("minimal",   "Minimal",   "personal",  "https://cdn.vyroportify.com/previews/minimal.png",   False),
    ("cyber",     "Cyber",     "developer", "https://cdn.vyroportify.com/previews/cyber.png",     True),
    ("executive", "Executive", "executive", "https://cdn.vyroportify.com/previews/executive.png", True),
]


def upgrade() -> None:
    bind = op.get_bind()
    for tid, name, category, preview, is_pro in _TEMPLATES:
        bind.execute(
            sa.text(
                """
                INSERT INTO templates (id, name, preview_url, category, is_pro,
                                       created_at, updated_at)
                VALUES (:id, :name, :preview_url, :category, :is_pro,
                        NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": tid,
                "name": name,
                "preview_url": preview,
                "category": category,
                "is_pro": is_pro,
            },
        )


def downgrade() -> None:
    # Only delete rows we know we inserted; leave community templates alone.
    bind = op.get_bind()
    for tid, *_ in _TEMPLATES:
        bind.execute(
            sa.text("DELETE FROM templates WHERE id = :id"),
            {"id": tid},
        )
