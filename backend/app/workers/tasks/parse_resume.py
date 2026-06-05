"""Celery task: download resume from S3, extract text, parse with Claude, update DB."""

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _parse_resume_async(resume_id: str) -> None:
    """Async implementation — runs inside asyncio.run() from the Celery task."""
    from app.database import AsyncSessionLocal
    from app.models.resume import Resume
    from app.services.resume_parser import (
        ResumeParseError,
        TextExtractionError,
        extract_text_from_docx,
        extract_text_from_pdf,
        parse_resume_with_claude,
    )
    from app.services.s3_service import storage

    resume_uuid = uuid.UUID(resume_id)

    async with AsyncSessionLocal() as db:
        resume = await db.get(Resume, resume_uuid)
        if resume is None:
            logger.error("Resume %s not found in DB", resume_id)
            return

        # ── 1. Mark processing ─────────────────────────────────────────────
        resume.status = "processing"
        await db.commit()

        try:
            # ── 2. Download from S3 ────────────────────────────────────────
            if not resume.s3_key:
                raise TextExtractionError("Resume has no s3_key")

            file_bytes = await storage.download_file(resume.s3_key)

            # ── 3. Extract text ────────────────────────────────────────────
            file_type = (resume.file_type or "").lower()
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(file_bytes)
            elif file_type in ("docx", "doc"):
                raw_text = extract_text_from_docx(file_bytes)
            else:
                # Fallback: try PDF first, then DOCX
                try:
                    raw_text = extract_text_from_pdf(file_bytes)
                except TextExtractionError:
                    raw_text = extract_text_from_docx(file_bytes)

            # ── 4. Parse with Claude ───────────────────────────────────────
            parsed = parse_resume_with_claude(raw_text)

            # ── 5. Save results ────────────────────────────────────────────
            resume.raw_text = raw_text
            resume.parsed_data = parsed.model_dump()
            resume.status = "done"
            await db.commit()

            logger.info("Resume %s parsed successfully", resume_id)

        except (TextExtractionError, ResumeParseError) as exc:
            logger.error("Resume %s parse failed: %s", resume_id, exc)
            resume.status = "failed"
            await db.commit()
            raise

        except Exception as exc:
            logger.exception("Resume %s unexpected error: %s", resume_id, exc)
            resume.status = "failed"
            await db.commit()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,        # exponential back-off: 30s, 60s, 120s
    retry_backoff_max=300,     # cap back-off at 5 minutes
    retry_jitter=True,         # add random jitter to avoid thundering herd
    # queue= removed: orphaned tasks on a no-listener queue
    acks_late=True,            # only ack after successful completion
    reject_on_worker_lost=True,  # re-queue if worker process is killed mid-task
)
def parse_resume_task(self, resume_id: str) -> dict:
    """Celery task to parse a resume asynchronously.

    Args:
        resume_id: UUID string of the resume to parse.

    Returns:
        Dict with status and resume_id.
    """
    logger.info("Starting parse_resume_task for resume_id=%s", resume_id)
    try:
        asyncio.run(_parse_resume_async(resume_id))
        return {"status": "done", "resume_id": resume_id}
    except Exception as exc:
        logger.error("Task failed for resume %s: %s", resume_id, exc)
        if self.request.retries >= self.max_retries:
            # Dead-letter: all retries exhausted — emit structured audit event
            from app.core.audit_log import log_security_event
            log_security_event(
                "TASK_DEAD_LETTER",
                user_id=None,
                detail={
                    "task": "parse_resume_task",
                    "resume_id": resume_id,
                    "retries": self.request.retries,
                    "error": str(exc)[:500],
                },
            )
            logger.error(
                "TASK_DEAD_LETTER parse_resume_task resume_id=%s after %d retries",
                resume_id,
                self.request.retries,
            )
            return {"status": "failed", "resume_id": resume_id}
        raise  # let autoretry_for handle the retry
