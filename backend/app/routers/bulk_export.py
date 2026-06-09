"""Bulk export of a user's portfolios as a streaming ZIP (v3.2.0).

GET /api/v1/bulk/portfolios.zip   ZIP containing each portfolio's content.json

For portfolios with `html_url` set, callers can fetch the rendered HTML
separately; the inline JSON snapshot is always included so the export is
self-contained even when S3 is offline.
"""

import io
import json
import logging
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.database import DB
from app.models.portfolio import Portfolio
from app.security import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bulk", tags=["Bulk Export"])

@router.get("/portfolios.zip")
async def bulk_portfolios_zip(db: DB, current_user: CurrentUser) -> StreamingResponse:
    
    from app.services.quota import consume as consume_quota
    await consume_quota(current_user, "bulk_export")

    rows = (
        await db.execute(
            select(Portfolio).where(Portfolio.user_id == current_user.id).order_by(Portfolio.created_at)
        )
    ).scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": str(current_user.id),
            "email": current_user.email,
            "portfolio_count": len(rows),
            "portfolios": [],
        }
        for p in rows:
            entry = {
                "id": str(p.id),
                "slug": p.slug,
                "status": p.status,
                "template_id": p.template_id,
                "views": p.views,
                "html_url": p.html_url,
                "custom_domain": p.custom_domain,
                "created_at": p.created_at.isoformat(),
            }
            manifest["portfolios"].append(entry)
            
            snapshot = {**entry, "content": p.content or {}}
            zf.writestr(f"portfolios/{p.slug}.json", json.dumps(snapshot, indent=2, default=str))

        zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))

    buf.seek(0)
    filename = f"vyroportify-export-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.zip"

    def _iter():
        yield from iter(lambda: buf.read(8192), b"")

    logger.info("bulk_export user=%s count=%d size=%d", current_user.id, len(rows), buf.getbuffer().nbytes)
    return StreamingResponse(
        _iter(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
