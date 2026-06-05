"""Outbound webhook management — Clerk-authenticated (v3.0.1).

Endpoints
---------
POST   /api/v1/webhooks                 Create endpoint (returns secret ONCE)
GET    /api/v1/webhooks                 List endpoints
GET    /api/v1/webhooks/{id}/deliveries Recent deliveries (audit)
DELETE /api/v1/webhooks/{id}            Delete endpoint
POST   /api/v1/webhooks/{id}/test       Dispatch a `ping` event
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select

from app.database import DB
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.security import CurrentUser
from app.services.webhooks import generate_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

ALLOWED_EVENTS = {
    "portfolio.published",
    "portfolio.failed",
    "subscription.changed",
    "resume.parsed",
    "ping",
    "*",
}


class CreateEndpointRequest(BaseModel):
    url: HttpUrl
    events: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=255)


class CreateEndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    description: str | None
    enabled: bool
    created_at: datetime
    secret: str  # only returned on creation


class EndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    description: str | None
    enabled: bool
    last_delivery_at: datetime | None
    created_at: datetime


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    event: str
    attempt: int
    status_code: int | None
    error: str | None
    delivered_at: datetime | None
    created_at: datetime


@router.post("", response_model=CreateEndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    body: CreateEndpointRequest, db: DB, current_user: CurrentUser
) -> CreateEndpointResponse:
    invalid = [e for e in body.events if e not in ALLOWED_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown events: {invalid}. Allowed: {sorted(ALLOWED_EVENTS)}",
        )
    secret = generate_secret()
    ep = WebhookEndpoint(
        user_id=current_user.id,
        url=str(body.url),
        secret=secret,
        events=",".join(body.events),
        description=body.description,
    )
    db.add(ep)
    await db.flush()
    await db.commit()
    await db.refresh(ep)
    return CreateEndpointResponse(
        id=ep.id,
        url=ep.url,
        events=ep.event_list(),
        description=ep.description,
        enabled=ep.enabled,
        created_at=ep.created_at,
        secret=secret,
    )


@router.get("", response_model=list[EndpointResponse])
async def list_endpoints(db: DB, current_user: CurrentUser) -> list[EndpointResponse]:
    result = await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.user_id == current_user.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return [
        EndpointResponse(
            id=e.id,
            url=e.url,
            events=e.event_list(),
            description=e.description,
            enabled=e.enabled,
            last_delivery_at=e.last_delivery_at,
            created_at=e.created_at,
        )
        for e in result.scalars().all()
    ]


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(endpoint_id: uuid.UUID, db: DB, current_user: CurrentUser) -> None:
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id, WebhookEndpoint.user_id == current_user.id
        )
    )
    ep = result.scalar_one_or_none()
    if ep is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    await db.delete(ep)
    await db.commit()


@router.get("/{endpoint_id}/deliveries", response_model=list[DeliveryResponse])
async def list_deliveries(
    endpoint_id: uuid.UUID, db: DB, current_user: CurrentUser
) -> list[DeliveryResponse]:
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if ep is None or ep.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == endpoint_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(50)
    )
    return [
        DeliveryResponse(
            id=d.id,
            event=d.event,
            attempt=d.attempt,
            status_code=d.status_code,
            error=d.error,
            delivered_at=d.delivered_at,
            created_at=d.created_at,
        )
        for d in result.scalars().all()
    ]


@router.get("/events")
async def list_event_catalog() -> dict:
    """v3.3.0 — Public catalog of every event type a subscriber can choose."""
    return {
        "events": [
            {"name": "portfolio.published", "description": "A portfolio finished generating and is live."},
            {"name": "portfolio.failed", "description": "Portfolio generation failed after all retries."},
            {"name": "subscription.changed", "description": "Stripe subscription created/updated/cancelled."},
            {"name": "resume.parsed", "description": "An uploaded resume finished parsing."},
            {"name": "ping", "description": "Manual test event from POST /webhooks/{id}/test."},
            {"name": "*", "description": "Wildcard — receive every event the user emits."},
        ],
        "signature_scheme": "X-VyroPortify-Signature: t=<unix>,v1=<hex_hmac_sha256> over `{t}.{body}`",
        "replay_window_seconds": 300,
    }


@router.post("/{endpoint_id}/deliveries/{delivery_id}/replay", status_code=status.HTTP_202_ACCEPTED)
async def replay_delivery(
    endpoint_id: uuid.UUID,
    delivery_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
) -> dict:
    """v3.3.0 — Re-dispatch a previously recorded delivery (forensics + replay).

    Useful when a receiver was down during the original window — the user can
    re-fire the exact same payload from the UI without crafting it manually.
    """
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if ep is None or ep.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    delivery = await db.get(WebhookDelivery, delivery_id)
    if delivery is None or delivery.endpoint_id != endpoint_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    from app.workers.tasks.deliver_webhook import deliver_webhook_task

    deliver_webhook_task.delay(
        endpoint_id=str(ep.id),
        event=delivery.event,
        data=(delivery.payload or {}).get("data", {}),
    )
    return {"enqueued": True, "replayed_delivery_id": str(delivery.id)}


@router.post("/{endpoint_id}/test", status_code=status.HTTP_202_ACCEPTED)
async def test_endpoint(endpoint_id: uuid.UUID, db: DB, current_user: CurrentUser) -> dict:
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if ep is None or ep.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    from app.workers.tasks.deliver_webhook import deliver_webhook_task

    deliver_webhook_task.delay(
        endpoint_id=str(ep.id),
        event="ping",
        data={"message": "hello from VyroPortify"},
    )
    return {"enqueued": True}
