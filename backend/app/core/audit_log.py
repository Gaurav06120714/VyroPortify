"""Structured security audit logging for VyroPortify.

Usage:
    from app.core.audit_log import log_security_event

    log_security_event(
        "auth_failure",
        user_id=None,
        detail={"reason": "invalid_token", "ip": request.client.host},
    )

Design principles:
  1. Never log PII — email addresses, passwords, API keys, card numbers must
     never appear in log lines. Use user_id (UUID) as the only identifier.
  2. JSON-structured output — makes logs parseable by Datadog, Splunk, CloudWatch,
     Loki, etc. without custom parsers.
  3. Fire-and-forget — log_security_event() never raises. A logging failure must
     not break the business flow that triggered it.
  4. Separate logger name ("vyroportify.security") so security events can be
     routed to a dedicated sink (e.g., a SIEM) via logging config.

Event types (expand as needed):
  auth_failure            JWT invalid / expired / not yet active
  auth_success            Successful Clerk JWT verification (optional, high volume)
  rate_limit_hit          SlowAPI rate-limit exceeded
  file_magic_mismatch     Uploaded file magic bytes don't match declared Content-Type
  file_size_exceeded      Upload exceeds configured size limit
  webhook_replay_blocked  Duplicate Stripe webhook event (idempotency cache hit)
  ai_input_truncated      User input truncated before sending to Claude
  ai_injection_detected   Prompt injection pattern found in user input
  config_validation_error Production startup blocked by misconfiguration
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

_security_logger = logging.getLogger("vyroportify.security")

if not _security_logger.handlers and not _security_logger.parent.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(message)s"))
    _security_logger.addHandler(_h)
    _security_logger.setLevel(logging.INFO)

def log_security_event(
    event_type: str,
    user_id: str | None,
    detail: dict[str, Any],
) -> None:
    """Emit a structured JSON security event to the security audit log.

    Args:
        event_type: Short snake_case event identifier (e.g. "auth_failure").
                    Must NOT contain PII.
        user_id:    Internal UUID of the acting user, or None for anonymous.
                    NEVER pass an email address — use the UUID only.
        detail:     Arbitrary key-value context.
                    MUST NOT contain: email, password, api_key, token, card number.
                    Safe to include: user_id, ip address, file extension,
                    http method, endpoint path, error code.

    This function is intentionally non-raising — a logging failure must not
    disrupt the business flow.
    """
    try:
        event: dict[str, Any] = {
            "ts": time.time(),
            "event": event_type,
            "user_id": user_id,  
            **_scrub_pii(detail),
        }
        _security_logger.info(json.dumps(event))
    except Exception:  
        
        _security_logger.warning(
            "audit_log failed to serialize event_type=%s user_id=%s",
            event_type,
            user_id,
        )

_PII_KEYS = frozenset({
    "email",
    "password",
    "hashed_password",
    "api_key",
    "anthropic_api_key",
    "stripe_secret_key",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "card_number",
    "cvv",
    "ssn",
    "phone",
})

def _scrub_pii(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove PII keys from a dict before logging.

    Any key matching _PII_KEYS (case-insensitive) is replaced with "[redacted]".
    This is a safety net — callers should not pass PII in the first place.
    """
    result: dict[str, Any] = {}
    for k, v in d.items():
        if k.lower() in _PII_KEYS:
            result[k] = "[redacted]"
        elif isinstance(v, dict):
            result[k] = _scrub_pii(v)
        else:
            result[k] = v
    return result
