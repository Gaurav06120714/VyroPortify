"""Celery task: deliver a single webhook event to one endpoint.

Retries on any 5xx or transport error using Celery's exponential backoff.
4xx responses are recorded but not retried (the receiver's fault).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.services.webhooks import serialize_payload, sign
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

def _sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace(
        "+psycopg", "+psycopg2"
    )
    return create_engine(url, future=True)

@celery_app.task(
    name="webhooks.deliver",
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=True,
    retry_backoff_max=3600,
    retry_jitter=True,
    max_retries=6,
    acks_late=True,
)
def deliver_webhook_task(*, endpoint_id: str, event: str, data: dict[str, Any]) -> dict:
    
    try:
        import redis as _sync_redis
        rc = _sync_redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        bucket_key = f"wh:rate:{endpoint_id}:{int(__import__('time').time() // 60)}"
        count = rc.incr(bucket_key)
        if count == 1:
            rc.expire(bucket_key, 120)
        if count > 60:
            logger.warning("webhook.throttled endpoint=%s minute_count=%d", endpoint_id, count)
            return {"throttled": True, "count": int(count)}
    except Exception as exc:
        logger.warning("webhook.rate_check_failed endpoint=%s err=%s", endpoint_id, exc)

    engine = _sync_engine()
    with Session(engine, future=True) as db:
        ep = db.get(WebhookEndpoint, uuid.UUID(endpoint_id))
        if ep is None or not ep.enabled:
            logger.info("webhook.skip endpoint=%s missing_or_disabled", endpoint_id)
            return {"skipped": True}

        body = serialize_payload(event, data)
        signature = sign(ep.secret, body)
        now = datetime.now(timezone.utc)

        delivery = WebhookDelivery(
            endpoint_id=ep.id, event=event, payload={"event": event, "data": data}, attempt=1
        )
        db.add(delivery)
        db.flush()

        try:
            resp = httpx.post(
                ep.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-VyroPortify-Event": event,
                    "X-VyroPortify-Signature": signature,
                    "X-VyroPortify-Delivery": str(delivery.id),
                    "User-Agent": "VyroPortify-Webhooks/1.0",
                },
                timeout=10,
            )
            delivery.status_code = resp.status_code
            delivery.response_body = (resp.text or "")[:2000]
            delivery.delivered_at = now
            ep.last_delivery_at = now
            db.commit()

            if 500 <= resp.status_code < 600:
                
                raise httpx.HTTPStatusError(
                    f"{resp.status_code}", request=resp.request, response=resp
                )
            return {"status_code": resp.status_code, "delivery_id": str(delivery.id)}
        except httpx.HTTPError as exc:
            delivery.error = str(exc)[:1000]
            db.commit()
            raise
