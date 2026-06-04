"""Celery task: dispatch a transactional email via Resend.

Kept dumb on purpose. Routers/webhooks call `send_email.delay(...)` and
forget; this task picks the template, builds it, and ships it. Retries are
configured at the task level — Resend's API is reliable but the network
between Celery workers and the API isn't.
"""

import logging
from typing import Any

from app.services import email_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


_TEMPLATE_FACTORIES = {
    "welcome": email_service.welcome,
    "portfolio_published": email_service.portfolio_published,
    "plan_changed": email_service.plan_changed,
    "payment_failed": email_service.payment_failed,
}


@celery_app.task(
    name="email.send",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def send_email_task(*, to: str, template_name: str, params: dict[str, Any]) -> bool:
    """Build a template by name and ship it. Returns the email_service result."""
    factory = _TEMPLATE_FACTORIES.get(template_name)
    if factory is None:
        logger.warning("send_email_task unknown template=%s", template_name)
        return False

    try:
        template = factory(**params)
    except TypeError as exc:
        # Bad call site — log loudly, don't retry, don't crash the worker.
        logger.error(
            "send_email_task bad params template=%s params=%s err=%s",
            template_name,
            params,
            exc,
        )
        return False

    return email_service.send_email_sync(to=to, template=template)
