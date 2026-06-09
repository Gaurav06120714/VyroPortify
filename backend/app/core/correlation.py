"""Correlation ID utilities.

A correlation ID is a UUID that tracks a single HTTP request through all layers
(middleware → router → service → worker). It is attached to every log line
and returned as X-Correlation-ID in every response header.

Usage:
    from app.core.correlation import get_correlation_id

    logger.info("event", extra={"correlation_id": get_correlation_id()})
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    """Return the current correlation ID, generating a new one if unset."""
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid

def set_correlation_id(cid: str) -> None:
    """Explicitly set the correlation ID (called from middleware)."""
    correlation_id_var.set(cid)
