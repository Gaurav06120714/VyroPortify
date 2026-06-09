"""Celery task: render a resume PDF, upload to R2/S3, mark the export row done.

Triggered by POST /api/v1/resume/{id}/export-pdf. The endpoint creates a
ResumeExport row with s3_key=NULL, dispatches this task, and returns
immediately so the caller can poll. ~95% of renders finish in under
2 seconds (reportlab path) and the user gets a presigned URL on the
first poll.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

async def _render_and_upload(export_id: str) -> None:
    from app.database import AsyncSessionLocal
    from app.models.resume import Resume
    from app.models.resume_export import ResumeExport
    from app.services.resume_pdf import ResumePayload, render_resume_pdf
    from app.services.s3_service import storage

    async with AsyncSessionLocal() as db:
        export = await db.get(ResumeExport, uuid.UUID(export_id))
        if export is None:
            logger.error("export_not_found id=%s", export_id)
            return
        resume = await db.get(Resume, export.resume_id)
        if resume is None or not resume.parsed_data:
            logger.error("export_no_parsed_data id=%s", export_id)
            return

        payload = ResumePayload(
            personal=resume.parsed_data.get("personal", {})
                or {
                    "full_name": resume.parsed_data.get("full_name"),
                    "email": resume.parsed_data.get("email"),
                    "phone": resume.parsed_data.get("phone"),
                    "location": resume.parsed_data.get("location"),
                    "title": resume.parsed_data.get("title"),
                },
            links=resume.parsed_data.get("links", {}),
            summary=resume.parsed_data.get("summary"),
            experience=resume.parsed_data.get("work_experience", []),
            education=resume.parsed_data.get("education", []),
            skills=resume.parsed_data.get("skills", []),
            projects=resume.parsed_data.get("projects", []),
            certifications=resume.parsed_data.get("certifications", []),
            achievements=resume.parsed_data.get("achievements", []),
        )

        result = render_resume_pdf(payload, template_id=export.template_id)

        s3_key = f"resume-exports/{export.user_id}/{export.content_hash}.pdf"
        await storage.upload_bytes(
            s3_key,
            result.pdf_bytes,
            content_type="application/pdf",
        )

        export.s3_key = s3_key
        export.file_size = len(result.pdf_bytes)
        export.engine = result.engine
        await db.commit()
        logger.info(
            "export_completed id=%s engine=%s bytes=%d",
            export_id, result.engine, len(result.pdf_bytes),
        )

@celery_app.task(
    name="resume.export_pdf",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=2,
    acks_late=True,
)
def export_resume_pdf(export_id: str) -> None:
    """Sync entry point — runs the async impl on a fresh event loop."""
    asyncio.run(_render_and_upload(export_id))
