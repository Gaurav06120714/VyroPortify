"""VyroPortify FastAPI application entry point.

Start the server:
    uvicorn app.main:app --reload --port 8000

Interactive docs (dev only):
    http://localhost:8000/api/v1/docs
    http://localhost:8000/api/v1/redoc
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.correlation import get_correlation_id, set_correlation_id
from app.core.exceptions import PortifyBaseException
from app.core.limiter import limiter
from app.core.security_config import security_settings
from app.core.sentry import init_sentry
from app.core.telemetry import init_otel
from app.routers import (
    admin_users,
    analytics,
    api_keys,
    auth,
    billing,
    bulk_export,
    clerk_webhook,
    compliance,
    connect,
    marketplace,
    oauth,
    organization,
    portfolio,
    public_api,
    resume,
    sso,
    webhooks,
)

init_sentry()

from app.core.logging_config import configure_logging
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-powered portfolio generator API",
    
    docs_url=f"{settings.API_V1_PREFIX}/docs" if not settings.is_production else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if not settings.is_production else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if not settings.is_production else None,
)

init_otel(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

@app.middleware("http")
async def enforce_request_size_limit(request: Request, call_next):
    """Reject requests with Content-Length exceeding MAX_REQUEST_BODY_BYTES.

    We check Content-Length first (fast path) and rely on the per-endpoint
    file read limits for chunked transfers without a Content-Length header.
    """
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
            if length > security_settings.MAX_REQUEST_BODY_BYTES:
                logger.warning(
                    "Request rejected: Content-Length %d > limit %d from %s",
                    length,
                    security_settings.MAX_REQUEST_BODY_BYTES,
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request body too large (max 10 MB)"},
                )
        except ValueError:
            pass  
    return await call_next(request)

_SUSPICIOUS_PATH_TOKENS = (
    "/wp-admin", "/wp-login", "/xmlrpc.php", "/.env", "/.git/",
    "/phpmyadmin", "/.aws/", "/.ssh/", "/etc/passwd",
)

@app.middleware("http")
async def ddos_hardening(request: Request, call_next):
    path = request.url.path
    
    low = path.lower()
    if any(tok in low for tok in _SUSPICIOUS_PATH_TOKENS):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        ua = request.headers.get("user-agent", "").strip()
        if not ua or len(ua) < 3:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing or invalid User-Agent header."},
            )

    response = await call_next(request)

    if path.startswith("/api/v1/portfolio/p/") or path.startswith("/portfolio/p/"):
        response.headers.setdefault("Cache-Control", "public, max-age=300, s-maxage=900")
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Attach security headers to every HTTP response.

    Headers and their rationale:
      X-Content-Type-Options: nosniff
          Prevents browsers from MIME-sniffing responses away from declared
          Content-Type. Stops attacks like serving a JS file as text/plain
          and having the browser execute it anyway.

      X-Frame-Options: DENY
          Prevents the API responses from being embedded in <iframe>.
          Protects against clickjacking attacks on authenticated API calls.

      X-XSS-Protection: 1; mode=block
          Legacy header for older IE/Edge browsers. Modern browsers have CSP,
          but this provides a safety net for clients that don't support CSP.

      Strict-Transport-Security: max-age=63072000; includeSubDomains
          Forces HTTPS for 2 years. Only sent in production to avoid breaking
          local HTTP development workflows.

      Referrer-Policy: strict-origin-when-cross-origin
          Prevents leaking the full URL (including query params/paths) to
          third-party origins. Full URL is sent only to same-origin requests.

      Permissions-Policy: camera=(), microphone=(), geolocation=()
          Explicitly disables sensitive device APIs. Protects users even if
          the frontend accidentally loads malicious third-party scripts.

      Content-Security-Policy:
          Controls which sources browsers allow for scripts, styles, images,
          and network connections. Significantly reduces XSS risk.
    """
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = security_settings.CONTENT_SECURITY_POLICY

    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Propagate or generate a correlation ID for every request."""
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    response.headers["X-Request-ID"] = cid  
    return response

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Attach X-Process-Time header to every response."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    return response

@app.exception_handler(PortifyBaseException)
async def portify_exception_handler(request: Request, exc: PortifyBaseException):
    """Convert all domain exceptions to structured JSON with correlation_id."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "error_code": exc.error_code,
            "correlation_id": get_correlation_id(),
        },
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": f"Route {request.method} {request.url.path} not found",
            "error_code": "NOT_FOUND",
            "correlation_id": get_correlation_id(),
        },
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception(
        "Unhandled server error on %s %s",
        request.method,
        request.url.path,
        extra={"correlation_id": get_correlation_id()},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "correlation_id": get_correlation_id(),
        },
    )

@app.on_event("startup")
async def on_startup() -> None:
    
    from app.core.config import validate_production_config
    validate_production_config()

    logger.info(
        "%s starting — environment=%s debug=%s",
        settings.APP_NAME,
        settings.ENVIRONMENT,
        settings.DEBUG,
        extra={"event": "startup"},
    )

@app.on_event("shutdown")
async def on_shutdown() -> None:
    from app.core.cache import cache
    from app.database import engine
    await cache.close()
    await engine.dispose()
    logger.info("Database engine disposed. Goodbye.")

app.include_router(auth.router,      prefix=settings.API_V1_PREFIX)
app.include_router(resume.router,    prefix=settings.API_V1_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_V1_PREFIX)
app.include_router(billing.router,      prefix=settings.API_V1_PREFIX)
app.include_router(organization.router, prefix=settings.API_V1_PREFIX)
app.include_router(marketplace.router,  prefix=settings.API_V1_PREFIX)
app.include_router(connect.router,      prefix=settings.API_V1_PREFIX)
app.include_router(api_keys.router,     prefix=settings.API_V1_PREFIX)
app.include_router(public_api.router,   prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router,     prefix=settings.API_V1_PREFIX)
app.include_router(oauth.router,        prefix=settings.API_V1_PREFIX)
app.include_router(compliance.router,   prefix=settings.API_V1_PREFIX)
app.include_router(sso.router,          prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router,    prefix=settings.API_V1_PREFIX)
app.include_router(bulk_export.router,  prefix=settings.API_V1_PREFIX)
app.include_router(clerk_webhook.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_users.router,   prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health() -> dict:
    """Returns 200 OK if the server process is alive. Used by load-balancer liveness checks."""
    return {"status": "ok", "version": "0.1.0", "environment": settings.ENVIRONMENT}

@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"], summary="Versioned liveness probe")
async def health_v1() -> dict:
    return {"status": "ok", "version": "0.1.0", "environment": settings.ENVIRONMENT}

@app.get(f"{settings.API_V1_PREFIX}/health/ready", tags=["Health"], summary="Readiness probe")
async def health_ready() -> JSONResponse:
    """Readiness probe — checks DB + Redis connectivity.

    Returns 200 when both are reachable, 503 if either fails.
    Used by Kubernetes readinessProbe / ECS health checks.
    """
    from sqlalchemy import text
    from app.database import AsyncSessionLocal
    from app.core.cache import cache

    result: dict[str, str] = {"db": "unknown", "redis": "unknown", "status": "unknown"}
    ok = True

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as exc:
        logger.error("Readiness check: DB ping failed: %s", exc)
        result["db"] = "error"
        ok = False

    try:
        await cache.client.ping()
        result["redis"] = "ok"
    except Exception as exc:
        logger.error("Readiness check: Redis ping failed: %s", exc)
        result["redis"] = "error"
        ok = False

    result["status"] = "ready" if ok else "degraded"
    return JSONResponse(
        status_code=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=result,
    )

@app.get(f"{settings.API_V1_PREFIX}/metrics/summary", tags=["Metrics"], summary="Non-sensitive runtime metrics")
async def metrics_summary() -> dict:
    """Return non-sensitive operational metrics.

    Intentionally coarse — does not expose user counts, revenue, or PII.
    Use Prometheus/Grafana for fine-grained metrics in production.
    """
    import os

    from app.core.cache import cache

    redis_info: dict = {}
    try:
        info = await cache.client.info("stats")
        redis_info = {
            "total_commands_processed": info.get("total_commands_processed"),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
            "rejected_connections": info.get("rejected_connections"),
        }
    except Exception:
        redis_info = {"error": "unavailable"}

    return {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "pid": os.getpid(),
        "redis": redis_info,
    }
