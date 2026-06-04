"""Transactional email service (Resend).

Thin HTTP wrapper around Resend's REST API. We deliberately do not pull in
the `resend` SDK — it adds another dependency for a single endpoint and the
SDK does no validation we can't trivially do here.

Design notes
------------
- The service is best-effort. Email is never on the critical path for billing
  or signup; a failure logs and returns, never raises into the caller.
- When RESEND_API_KEY is empty the service no-ops with a log line. That keeps
  local dev and CI green without conditional logic at every call site.
- For volume / retry safety the actual send is dispatched via a Celery task
  (`workers.tasks.send_email`). Direct `send_email_sync` exists for tests
  and for paths where async dispatch isn't worth the complexity.
- Templates are inline HTML. Until we ship more than ~6 emails it's not
  worth building a Jinja loader for this surface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class EmailTemplate:
    subject: str
    html: str


# ── Templates ──────────────────────────────────────────────────────────────────

def welcome(name: str) -> EmailTemplate:
    safe_name = (name or "there").strip()[:80]
    return EmailTemplate(
        subject="Welcome to VyroPortify ⚡",
        html=(
            f"<p>Hey {safe_name},</p>"
            "<p>Welcome to VyroPortify. Upload a resume and you'll have a "
            "live portfolio in under 60 seconds.</p>"
            f'<p><a href="{settings.FRONTEND_URL}/dashboard">Open your dashboard →</a></p>'
            "<p>— The VyroPortify team</p>"
        ),
    )


def portfolio_published(name: str, public_url: str) -> EmailTemplate:
    safe_name = (name or "there").strip()[:80]
    return EmailTemplate(
        subject="Your portfolio is live 🚀",
        html=(
            f"<p>Hey {safe_name},</p>"
            f'<p>Your portfolio is published: <a href="{public_url}">{public_url}</a></p>'
            "<p>Share it on LinkedIn, in your bio, or wherever your next role finds you.</p>"
        ),
    )


def plan_changed(name: str, new_plan: str) -> EmailTemplate:
    safe_name = (name or "there").strip()[:80]
    pretty = new_plan.title()
    return EmailTemplate(
        subject=f"You're now on the {pretty} plan",
        html=(
            f"<p>Hey {safe_name},</p>"
            f"<p>Your VyroPortify plan changed to <strong>{pretty}</strong>.</p>"
            "<p>Pro perks: unlimited portfolios, all templates, AI cover letters, "
            "and custom domains.</p>"
            f'<p><a href="{settings.FRONTEND_URL}/dashboard/settings/billing">Manage billing →</a></p>'
        ),
    )


def payment_failed(name: str) -> EmailTemplate:
    safe_name = (name or "there").strip()[:80]
    return EmailTemplate(
        subject="Payment issue on your VyroPortify subscription",
        html=(
            f"<p>Hey {safe_name},</p>"
            "<p>We couldn't charge the card on file for your Pro subscription. "
            "Update your payment method to keep Pro features active.</p>"
            f'<p><a href="{settings.FRONTEND_URL}/dashboard/settings/billing">Update payment →</a></p>'
        ),
    )


# ── Send ───────────────────────────────────────────────────────────────────────

def _post_resend(payload: dict[str, Any]) -> bool:
    """Best-effort POST to Resend. Returns True if accepted."""
    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            resp = client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code >= 400:
            logger.warning(
                "resend_send_failed status=%s body=%s", resp.status_code, resp.text[:300]
            )
            return False
        return True
    except httpx.HTTPError as exc:
        logger.warning("resend_send_error: %s", exc)
        return False


def send_email_sync(*, to: str, template: EmailTemplate) -> bool:
    """Send an email synchronously. Returns True on success, False on no-op or failure.

    No-ops (returns False) when RESEND_API_KEY is unset — useful for local dev
    and tests so call sites don't need to gate on configuration.
    """
    if not settings.RESEND_API_KEY:
        logger.info("email_skipped no_resend_key to=%s subject=%s", to, template.subject)
        return False

    if not to or "@" not in to:
        logger.warning("email_skipped invalid_address to=%r", to)
        return False

    return _post_resend(
        {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": template.subject,
            "html": template.html,
        }
    )
