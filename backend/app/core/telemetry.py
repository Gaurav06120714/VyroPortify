"""OpenTelemetry bootstrap (v1.5.0).

Wires OTLP exporters when OTEL_EXPORTER_OTLP_ENDPOINT is set. Off-by-default
so dev/CI don't need a collector running. Instruments FastAPI, SQLAlchemy,
HTTPX, and Celery automatically if the corresponding contrib packages are
installed; missing packages are reported as a warning and skipped.

This module deliberately does no heavy work at import — `init_otel(app)` is
the single entry point and is called from app.main:create_app().
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    
    return bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

def _safe_import(modname: str) -> Any | None:
    try:
        return __import__(modname, fromlist=["*"])
    except ImportError:
        return None

def init_otel(app: Any) -> None:
    """Bootstrap OTel. Safe to call when the SDK isn't installed."""
    if not _enabled():
        logger.info("otel_disabled — set OTEL_EXPORTER_OTLP_ENDPOINT to enable")
        return

    sdk = _safe_import("opentelemetry.sdk.trace")
    exporter_mod = _safe_import("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    api = _safe_import("opentelemetry")
    res_mod = _safe_import("opentelemetry.sdk.resources")

    if not (sdk and exporter_mod and api and res_mod):
        logger.warning(
            "otel_packages_missing — install opentelemetry-sdk and "
            "opentelemetry-exporter-otlp-proto-http to enable tracing"
        )
        return

    resource = res_mod.Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "vyroportify-api"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )
    provider = sdk.TracerProvider(resource=resource)
    provider.add_span_processor(
        sdk.BatchSpanProcessor(exporter_mod.OTLPSpanExporter())
    )
    api.trace.set_tracer_provider(provider)

    for mod_name, instrument in (
        ("opentelemetry.instrumentation.fastapi", "FastAPIInstrumentor"),
        ("opentelemetry.instrumentation.sqlalchemy", "SQLAlchemyInstrumentor"),
        ("opentelemetry.instrumentation.httpx", "HTTPXClientInstrumentor"),
        ("opentelemetry.instrumentation.celery", "CeleryInstrumentor"),
    ):
        mod = _safe_import(mod_name)
        if mod is None:
            logger.info("otel_skip module=%s (not installed)", mod_name)
            continue
        cls = getattr(mod, instrument, None)
        if cls is None:
            continue
        try:
            if instrument == "FastAPIInstrumentor":
                cls().instrument_app(app)
            else:
                cls().instrument()
        except Exception as exc:
            logger.warning("otel_instrument_failed module=%s err=%s", mod_name, exc)

    logger.info("otel_initialized service=%s", os.getenv("OTEL_SERVICE_NAME", "vyroportify-api"))
