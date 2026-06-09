"""Structured logging configuration for VyroPortify.

In production (ENVIRONMENT=production):
  - Emits JSON lines with timestamp, level, correlation_id, event, etc.
  - Never logs: email, api_key, token, password.

In development:
  - Emits human-readable lines.

Call configure_logging() once at startup (main.py on_startup).

Usage:
    from app.core.logging_config import configure_logging
    configure_logging()
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings

_PII_KEYS = frozenset({
    "email", "password", "hashed_password", "api_key", "token",
    "access_token", "refresh_token", "secret", "card_number",
})

class _JSONFormatter(logging.Formatter):
    """Emit a single JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:  
        from app.core.correlation import get_correlation_id

        payload: dict[str, Any] = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        for key, value in record.__dict__.items():
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "id", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg", "name",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "taskName",
            ):
                continue
            if key.lower() in _PII_KEYS:
                payload[key] = "[redacted]"
            else:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)

class _DevFormatter(logging.Formatter):
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

    def __init__(self) -> None:
        super().__init__(self.fmt, datefmt="%H:%M:%S")

def configure_logging() -> None:
    """Configure root logger with the appropriate formatter.

    Call once at application startup. Idempotent (guards against double-call).
    """
    root = logging.getLogger()

    if getattr(root, "_portify_configured", False):
        return

    formatter: logging.Formatter = (
        _JSONFormatter() if settings.is_production else _DevFormatter()
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO_SQL else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    root._portify_configured = True  
