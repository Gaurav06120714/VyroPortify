"""Outbound webhook signing + dispatch helpers (v3.0.1).

Signature scheme — `X-VyroPortify-Signature: t=<unix>,v1=<hex>`
where v1 = HMAC_SHA256(secret, f"{t}.{body}").

Receivers verify by recomputing v1 over the same string. The timestamp guards
against replay (receivers should reject if abs(now - t) > 5 minutes).
"""

import hmac
import hashlib
import json
import secrets
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookEndpoint


def generate_secret() -> str:
    return secrets.token_hex(32)


def sign(secret: str, body: str, timestamp: int | None = None) -> str:
    t = timestamp if timestamp is not None else int(time.time())
    mac = hmac.new(
        secret.encode("utf-8"),
        f"{t}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={t},v1={mac}"


def serialize_payload(event: str, data: dict[str, Any]) -> str:
    return json.dumps({"event": event, "data": data}, sort_keys=True, default=str)


async def matching_endpoints(
    db: AsyncSession, user_id, event: str
) -> list[WebhookEndpoint]:
    """Return enabled endpoints owned by user that subscribe to `event`."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.user_id == user_id,
            WebhookEndpoint.enabled.is_(True),
        )
    )
    return [e for e in result.scalars().all() if event in e.event_list() or "*" in e.event_list()]


async def emit(db: AsyncSession, user_id, event: str, data: dict[str, Any]) -> int:
    """Find matching endpoints and enqueue a delivery task for each.

    Returns the number of dispatch tasks enqueued.
    """
    from app.workers.tasks.deliver_webhook import deliver_webhook_task

    endpoints = await matching_endpoints(db, user_id, event)
    for ep in endpoints:
        deliver_webhook_task.delay(endpoint_id=str(ep.id), event=event, data=data)
    return len(endpoints)
