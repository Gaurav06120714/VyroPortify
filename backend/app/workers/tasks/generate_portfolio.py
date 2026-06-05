"""Celery task: enhance content, render template, save HTML to S3, update Portfolio DB record."""

import asyncio
import logging
import re
import time
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug[:60]


async def _generate_async(portfolio_id: str) -> None:
    from app.database import AsyncSessionLocal
    from app.models.portfolio import Portfolio
    from app.models.resume import Resume
    from app.services.portfolio_generator import content_enhancer, template_injector
    from app.services.s3_service import storage

    portfolio_uuid = uuid.UUID(portfolio_id)

    async with AsyncSessionLocal() as db:
        portfolio = await db.get(Portfolio, portfolio_uuid)
        if portfolio is None:
            logger.error("Portfolio %s not found", portfolio_id)
            return

        portfolio.status = "generating"  # PortfolioStatus.GENERATING.value
        await db.commit()

        t_start = time.monotonic()

        try:
            # ── 1. Get resume parsed_data ──────────────────────────────────
            resume = await db.get(Resume, portfolio.resume_id)
            if resume is None or not resume.parsed_data:
                raise ValueError(f"Resume {portfolio.resume_id} has no parsed_data")

            parsed_data: dict = resume.parsed_data

            # ── 2. Enhance with Claude ─────────────────────────────────────
            enhanced = content_enhancer.enhance(parsed_data)

            # ── 3. Render template ─────────────────────────────────────────
            template_id = portfolio.template_id or "aurora"
            html = template_injector.inject(template_id, parsed_data, enhanced)

            # ── 4. Upload HTML to S3 ───────────────────────────────────────
            html_bytes = html.encode("utf-8")
            name = parsed_data.get("full_name", "portfolio")
            s3_key = f"portfolios/{portfolio.user_id}/{portfolio.slug}/index.html"

            # Store inline — public-readable HTML
            try:
                await storage.upload_file(
                    data=html_bytes,
                    user_id=portfolio.user_id,
                    filename="index.html",
                    content_type="text/html; charset=utf-8",
                )
                html_url = await storage.presigned_url(s3_key, ttl_hours=24 * 365)
            except Exception as exc:
                logger.warning("S3 upload failed for portfolio %s: %s — storing inline", portfolio_id, exc)
                html_url = None

            # ── 5. Build content snapshot ──────────────────────────────────
            content_snapshot = {
                **parsed_data,
                **enhanced,
                "template_id": template_id,
            }

            # ── 6. Save results ────────────────────────────────────────────
            portfolio.content = content_snapshot
            portfolio.html_url = html_url
            portfolio.status = "published"  # PortfolioStatus.PUBLISHED.value
            duration_ms = int((time.monotonic() - t_start) * 1000)

            await db.commit()
            logger.info("Portfolio %s generated in %dms", portfolio_id, duration_ms)

            # v3.0.1 — outbound webhook: portfolio.published
            try:
                from app.services.webhooks import emit as emit_webhook
                await emit_webhook(
                    db,
                    portfolio.user_id,
                    "portfolio.published",
                    {
                        "portfolio_id": str(portfolio.id),
                        "slug": portfolio.slug,
                        "html_url": portfolio.html_url,
                        "template_id": portfolio.template_id,
                    },
                )
            except Exception as wh_exc:
                logger.warning("portfolio.published webhook emit failed: %s", wh_exc)

        except Exception as exc:
            logger.exception("Portfolio %s generation failed: %s", portfolio_id, exc)
            portfolio.status = "failed"  # PortfolioStatus.FAILED.value
            await db.commit()
            try:
                from app.services.webhooks import emit as emit_webhook
                await emit_webhook(
                    db,
                    portfolio.user_id,
                    "portfolio.failed",
                    {"portfolio_id": str(portfolio.id), "error": str(exc)[:300]},
                )
            except Exception:
                pass
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,        # exponential back-off: 30s, 60s, 120s
    retry_backoff_max=300,     # cap back-off at 5 minutes
    retry_jitter=True,         # jitter to spread retries across workers
    # No `queue=` override: Celery's default is `celery`, and the
    # worker (started without -Q) listens there. Setting
    # queue="default" pushed tasks onto a queue no worker consumed,
    # leaving the UI stuck on "Almost Ready!" forever while the
    # message sat untouched in Redis.
    acks_late=True,            # only ack after successful completion
    reject_on_worker_lost=True,  # re-queue if worker is killed mid-task
)
def generate_portfolio_task(self, portfolio_id: str) -> dict:
    """Celery task to generate a portfolio from an already-parsed resume.

    Args:
        portfolio_id: UUID string of the Portfolio record.
    """
    logger.info("Starting generate_portfolio_task for portfolio_id=%s", portfolio_id)
    try:
        asyncio.run(_generate_async(portfolio_id))
        return {"status": "published", "portfolio_id": portfolio_id}
    except Exception as exc:
        logger.error("generate_portfolio_task failed for %s: %s", portfolio_id, exc)
        if self.request.retries >= self.max_retries:
            # Dead-letter: all retries exhausted — emit structured audit event
            from app.core.audit_log import log_security_event
            log_security_event(
                "TASK_DEAD_LETTER",
                user_id=None,
                detail={
                    "task": "generate_portfolio_task",
                    "portfolio_id": portfolio_id,
                    "retries": self.request.retries,
                    "error": str(exc)[:500],
                },
            )
            logger.error(
                "TASK_DEAD_LETTER generate_portfolio_task portfolio_id=%s after %d retries",
                portfolio_id,
                self.request.retries,
            )
            return {"status": "failed", "portfolio_id": portfolio_id}
        raise  # let autoretry_for handle the retry
