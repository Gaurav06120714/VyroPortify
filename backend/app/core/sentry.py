"""Sentry SDK initialisation for the backend.

Import and call ``init_sentry()`` once at app startup (e.g. in ``main.py``).
If ``SENTRY_DSN`` is empty the function is a harmless no-op.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_initialized = False

def init_sentry() -> None:
    global _initialized
    if _initialized:
        return

    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        logger.info("SENTRY_DSN not set — Sentry disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        environment = os.getenv("ENVIRONMENT", "development")
        traces_sample_rate = 0.2 if environment == "production" else 1.0

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                CeleryIntegration(monitor_beat_tasks=True),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
        )
        _initialized = True
        logger.info("Sentry initialised (env=%s, traces=%.1f)", environment, traces_sample_rate)
    except ImportError:
        logger.warning("sentry-sdk not installed — Sentry disabled.")
