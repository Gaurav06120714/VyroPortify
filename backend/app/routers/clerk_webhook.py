"""Clerk → backend user mirror (v3.4.0).

Clerk owns the entire auth UX — password, email OTP, phone OTP, Google,
GitHub, "forgot password" — out of the box. This webhook keeps our `users`
table in lockstep with Clerk so admin export, billing, and analytics see
every signup the moment it lands, not lazily on first authenticated call.

Configure in Clerk dashboard
----------------------------
1. Settings → Webhooks → "Add Endpoint"
2. URL: https://<your-api-host>/api/v1/auth/clerk-webhook
3. Subscribe to events: user.created, user.updated, user.deleted
4. Copy the Signing Secret → `CLERK_WEBHOOK_SECRET` in backend .env

Security
--------
Every request must pass svix signature verification with the shared secret;
no fallback "warn-and-accept" path. If the secret is unset we 503 so a
misconfig is loud rather than silent.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.audit_log import log_security_event
from app.core.config import settings
from app.core.enums import Plan
from app.database import DB
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


def _primary_email(payload: dict) -> str | None:
    eid = payload.get("primary_email_address_id")
    for e in payload.get("email_addresses", []) or []:
        if e.get("id") == eid or eid is None:
            return e.get("email_address")
    return None


def _primary_phone(payload: dict) -> str | None:
    pid = payload.get("primary_phone_number_id")
    for p in payload.get("phone_numbers", []) or []:
        if p.get("id") == pid or pid is None:
            return p.get("phone_number")
    return None


def _full_name(payload: dict) -> str | None:
    first = (payload.get("first_name") or "").strip()
    last = (payload.get("last_name") or "").strip()
    name = f"{first} {last}".strip()
    return name or payload.get("username") or None


@router.post("/clerk-webhook", status_code=status.HTTP_200_OK)
async def clerk_webhook(request: Request, db: DB) -> dict:
    if not settings.CLERK_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_WEBHOOK_SECRET not configured",
        )

    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        event = wh.verify(body, headers)
    except WebhookVerificationError as exc:
        log_security_event(
            "clerk_webhook_invalid_signature", user_id=None, detail={"error": str(exc)[:200]}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    event_type = event.get("type", "")
    data = event.get("data", {})
    clerk_id = data.get("id")
    if not clerk_id:
        return {"ignored": True}

    if event_type in ("user.created", "user.updated"):
        email = _primary_email(data) or f"{clerk_id}@clerk.local"
        phone = _primary_phone(data)
        name = _full_name(data)

        existing = (
            await db.execute(select(User).where(User.clerk_user_id == clerk_id))
        ).scalar_one_or_none()

        if existing is None:
            user = User(
                clerk_user_id=clerk_id,
                email=email,
                name=name,
                phone_number=phone,
                plan=Plan.FREE,
            )
            db.add(user)
            await db.flush()
            logger.info("clerk_webhook user_created clerk_id=%s", clerk_id)
            # Mirror the personal-org bootstrap that happens in security.py on
            # first authenticated call, so users created via the Clerk hosted UI
            # immediately have a workspace + membership.
            from app.models.organization import Membership, Organization

            owner_label = name or email.split("@")[0]
            org = Organization(
                name=f"{owner_label}'s Workspace",
                slug=f"personal-{str(user.id)[:8]}",
                is_personal=True,
                plan=user.plan,
            )
            db.add(org)
            await db.flush()
            db.add(Membership(organization_id=org.id, user_id=user.id, role="owner"))
        else:
            existing.email = email
            existing.name = name or existing.name
            if phone:
                existing.phone_number = phone

        await db.commit()
        return {"status": "ok", "event": event_type}

    if event_type == "user.deleted":
        existing = (
            await db.execute(select(User).where(User.clerk_user_id == clerk_id))
        ).scalar_one_or_none()
        if existing is not None:
            log_security_event(
                "clerk_webhook_user_deleted",
                user_id=str(existing.id),
                detail={"clerk_id": clerk_id, "deleted_at": datetime.now(timezone.utc).isoformat()},
            )
            await db.delete(existing)
            await db.commit()
        return {"status": "ok", "event": event_type}

    return {"ignored": True, "event": event_type}
