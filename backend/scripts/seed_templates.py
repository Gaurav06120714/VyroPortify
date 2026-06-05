"""Seed the four canonical portfolio templates.

Usage (from /backend with .venv active):
    python -m scripts.seed_templates

The script is fully idempotent — INSERT … ON CONFLICT DO UPDATE so it is safe
to re-run any number of times. Existing rows are updated in-place if config
has changed.

The four IDs match app.core.enums.TemplateID and the on-disk template
directories at app/templates/{aurora,minimal,cyber,executive}/.
The previous seeder shipped with stale ids (minimal/modern/bold) which
caused POST /portfolio/generate to 5xx with a FK violation when the
frontend asked for `aurora`.
"""

import asyncio
import sys
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.models.template import Template

# ── seed data ─────────────────────────────────────────────────────────────────

DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "aurora",
        "name": "Aurora",
        "preview_url": "https://cdn.vyroportify.com/previews/aurora.png",
        "category": "developer",
        "is_pro": False,
        "config": {
            "layout": "single-column",
            "fonts": {"heading": "Inter", "body": "Inter"},
            "colors": {
                "primary": "#0a0a14",
                "accent": "#7c5cff",
                "background": "#0a0a14",
                "surface": "#13131e",
                "text": "#f5f5fa",
            },
            "sections": {
                "hero": True, "about": True, "experience": True,
                "education": True, "skills": True, "projects": True,
                "awards": False, "contact": True,
            },
            "border_radius": "0.75rem",
            "spacing": "comfortable",
        },
    },
    {
        "id": "minimal",
        "name": "Minimal",
        "preview_url": "https://cdn.vyroportify.com/previews/minimal.png",
        "category": "personal",
        "is_pro": False,
        "config": {
            "layout": "single-column",
            "fonts": {"heading": "Inter", "body": "Inter"},
            "colors": {
                "primary": "#111827",
                "accent": "#6366f1",
                "background": "#ffffff",
                "surface": "#f9fafb",
                "text": "#374151",
            },
            "sections": {
                "hero": True, "about": True, "experience": True,
                "education": True, "skills": True, "projects": False,
                "awards": False, "contact": True,
            },
            "border_radius": "0.375rem",
            "spacing": "comfortable",
        },
    },
    {
        "id": "cyber",
        "name": "Cyber",
        "preview_url": "https://cdn.vyroportify.com/previews/cyber.png",
        "category": "developer",
        "is_pro": True,
        "config": {
            "layout": "single-column",
            "fonts": {"heading": "Space Grotesk", "body": "JetBrains Mono"},
            "colors": {
                "primary": "#000000",
                "accent": "#00ff9c",
                "background": "#0a0a0a",
                "surface": "#141414",
                "text": "#e6e6e6",
            },
            "sections": {
                "hero": True, "about": True, "experience": True,
                "education": True, "skills": True, "projects": True,
                "awards": True, "contact": True,
            },
            "border_radius": "0.25rem",
            "spacing": "compact",
        },
    },
    {
        "id": "executive",
        "name": "Executive",
        "preview_url": "https://cdn.vyroportify.com/previews/executive.png",
        "category": "executive",
        "is_pro": True,
        "config": {
            "layout": "two-column",
            "fonts": {"heading": "Playfair Display", "body": "Source Sans Pro"},
            "colors": {
                "primary": "#1a1a2e",
                "accent": "#c8a96a",
                "background": "#fafaf9",
                "surface": "#f5f0e8",
                "text": "#292524",
            },
            "sections": {
                "hero": True, "about": True, "experience": True,
                "education": True, "skills": True, "projects": True,
                "awards": True, "contact": True,
            },
            "border_radius": "0rem",
            "spacing": "spacious",
        },
    },
]


# ── seed logic ────────────────────────────────────────────────────────────────

async def seed() -> None:
    """Upsert all default templates (idempotent)."""
    async with AsyncSessionLocal() as session:
        stmt = (
            pg_insert(Template)
            .values(DEFAULT_TEMPLATES)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": pg_insert(Template).excluded.name,
                    "preview_url": pg_insert(Template).excluded.preview_url,
                    "category": pg_insert(Template).excluded.category,
                    "is_pro": pg_insert(Template).excluded.is_pro,
                    "config": pg_insert(Template).excluded.config,
                    # updated_at is handled by SQLAlchemy's onupdate
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    ids = [t["id"] for t in DEFAULT_TEMPLATES]
    print(f"✓ Upserted {len(ids)} template(s): {ids}", flush=True)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
