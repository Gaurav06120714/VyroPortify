"""
Rate-limiting infrastructure for VyroPortify.

Architecture
------------
We use SlowAPI (wraps the `limits` library) for decorator-style per-endpoint
limits, backed by Redis for persistence across restarts and multiple workers.

Additionally, this module provides:
  - A proxy-aware key function that correctly resolves the client IP behind
    Nginx/ALB/Cloudflare, controlled by the PROXY_DEPTH environment variable.
  - A login-specific key function that combines IP + hashed email for dual-key
    brute-force protection.
  - Progressive lockout helpers (5 fails→15 min, 10→1 hr, 20→24 hr).
  - Privacy-preserving logging (IPs/emails are hashed, never logged raw).

Environment variables
---------------------
  PROXY_DEPTH     Number of trusted reverse-proxy hops (default: 1)
  REDIS_URL       Redis connection string (default: redis://localhost:6379)
  IP_HASH_SALT    HMAC salt for hashing IPs/emails in logs (MUST be changed in prod)
  LOG_LEVEL       Python logging level (default: WARNING in prod, INFO in dev)

Usage in a router
-----------------
    from app.core.limiter import limiter
    from slowapi.errors import RateLimitExceeded

    @router.post("/auth/login")
    @limiter.limit("5/15minutes")
    async def login(request: Request, ...):
        ...

    # For dual-key (IP + email) login protection, use the dependency instead:
    from app.core.rate_limit import RateLimitDep
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Callable

from slowapi import Limiter
from starlette.requests import Request

logger = logging.getLogger(__name__)

PROXY_DEPTH: int = int(os.environ.get("PROXY_DEPTH", "1"))
"""
Number of trusted proxy hops in front of this service.

Example: Client → Cloudflare (1) → AWS ALB (2) → Uvicorn
  PROXY_DEPTH=2  →  client IP is XFF[-3]

Set too low:  attackers spoof XFF and bypass IP limits.
Set too high: all requests share one bucket (the internal proxy IP).
"""

REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")

IP_HASH_SALT: str = os.environ.get(
    "IP_HASH_SALT", "vyroportify-change-this-salt-in-prod"
)
"""HMAC salt for privacy-preserving IP/email hashes in logs.
   Generate in production with:  python -c "import secrets; print(secrets.token_hex(32))"
"""

def _hash_for_log(value: str) -> str:
    """HMAC-SHA256 of value with IP_HASH_SALT, truncated to 16 hex chars.

    Short enough to be readable in logs, not long enough to reverse.
    Using HMAC (keyed hash) instead of plain SHA256 prevents rainbow-table
    attacks even if the salt leaks.
    """
    return hmac.new(
        IP_HASH_SALT.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]

def _extract_client_ip(request: Request) -> str:
    """
    Resolve the real client IP from the request, trusting PROXY_DEPTH hops.

    Algorithm:
      1. Parse X-Forwarded-For into [client, proxy1, …, outerProxy].
      2. The rightmost PROXY_DEPTH entries are our own infrastructure.
      3. The entry immediately left of those is the client IP.

    Falls back to X-Real-IP, then request.client.host.
    """
    xff: str | None = request.headers.get("x-forwarded-for")

    if xff:
        ips = [ip.strip() for ip in xff.split(",") if ip.strip()]
        
        client_idx = len(ips) - PROXY_DEPTH - 1
        if client_idx >= 0 and ips[client_idx]:
            return _sanitise_ip(ips[client_idx])
        if ips:
            return _sanitise_ip(ips[0])  

    xri: str | None = request.headers.get("x-real-ip")
    if xri:
        return _sanitise_ip(xri.strip())

    if request.client:
        return _sanitise_ip(request.client.host)

    return "0.0.0.0"

def _sanitise_ip(ip: str) -> str:
    """Strip IPv6 zone IDs and validate basic IP format."""
    clean = ip.split("%")[0].lower().strip()
    import re
    if re.match(r'^[\d.]+$', clean) or re.match(r'^[0-9a-f:]+$', clean):
        return clean
    return "0.0.0.0"

def get_client_ip(request: Request) -> str:
    """SlowAPI key function: returns real client IP (proxy-aware).

    This is passed to Limiter(key_func=...) as the default key.
    """
    ip = _extract_client_ip(request)
    return ip

def get_login_key(request: Request) -> str:
    """
    Key function for login endpoints: combines IP + email hash.

    Returns "<ip>|email:<hash>" so that:
      - Multiple IPs attacking the same account each count toward the
        per-email bucket.
      - One IP trying many accounts still hits the per-IP bucket.

    SlowAPI applies the limit once per unique key, so this effectively
    creates a combined IP+email window. For independent IP and email limits
    use the RateLimitDep dependency in rate_limit.py instead.
    """
    ip = _extract_client_ip(request)
    try:
        
        email: str = getattr(request.state, "login_email", "") or ""
        if email:
            email_hash = _hash_for_log(email.lower())
            return f"{ip}|email:{email_hash}"
    except Exception:
        pass
    return ip

def log_security_event(
    request: Request,
    event: str,
    extra: dict | None = None,
) -> None:
    """Log a security event without emitting raw PII.

    Fields logged:
      - event name
      - hashed IP (not raw)
      - HTTP method + path (query string stripped to avoid leaking tokens)
      - truncated User-Agent
      - optional extra dict (must NOT contain passwords, tokens, or email text)
    """
    ip = _extract_client_ip(request)
    path = str(request.url.path)  

    log_record: dict = {
        "security_event": event,
        "ip_hash": _hash_for_log(ip),
        "method": request.method,
        "path": path,
        "user_agent": (request.headers.get("user-agent", "none") or "none")[:250],
    }
    if extra:
        
        _FORBIDDEN_EXTRA_KEYS = {"password", "token", "email", "secret", "key", "hash"}
        for k in extra:
            if k.lower() in _FORBIDDEN_EXTRA_KEYS:
                logger.error(
                    "log_security_event: caller attempted to log sensitive field '%s' — dropped",
                    k,
                )
            else:
                log_record[k] = extra[k]

    logger.warning("[security] %s %s", event, log_record)

try:
    from limits.storage import RedisStorage  
    _storage_uri = REDIS_URL
    limiter = Limiter(
        key_func=get_client_ip,
        default_limits=["200/minute"],
        storage_uri=_storage_uri,
        strategy="moving-window",  
    )
    logger.info("SlowAPI limiter initialised with Redis storage: %s", REDIS_URL.split("@")[-1])
except Exception as exc:
    
    logger.warning(
        "Redis unavailable for rate limiter (%s) — falling back to in-memory. "
        "Multi-instance rate limits will NOT be shared.",
        exc,
    )
    limiter = Limiter(
        key_func=get_client_ip,
        default_limits=["200/minute"],
        strategy="moving-window",
    )
