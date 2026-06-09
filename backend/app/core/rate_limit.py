"""
Advanced rate-limiting dependency for VyroPortify.

Provides:
  - Redis sliding-window check (pure Python, no SlowAPI dependency)
  - Progressive lockout for authentication endpoints
  - FastAPI dependency functions for per-route enforcement
  - Dual-key (IP + hashed email) login protection

All Redis operations are fire-and-forget with graceful fallback:
if Redis is unavailable, the request is allowed through with a warning log.
This is intentional — a Redis outage should degrade security posture, not
take down the entire service.

Usage
-----
    from app.core.rate_limit import (
        check_login_rate_limit,
        record_login_failure,
        record_login_success,
        RateLimitCheck,
    )

    @router.post("/auth/login")
    async def login(
        body: LoginBody,
        request: Request,
        _rl: None = Depends(RateLimitCheck("login", max_per_ip=5, window_seconds=900)),
    ):
        ...
        if not valid:
            await record_login_failure(request, body.email)
            raise HTTPException(401, "Invalid credentials")
        await record_login_success(request, body.email)
        ...
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)

from app.core.limiter import (
    IP_HASH_SALT,
    _extract_client_ip,
    _hash_for_log,
    log_security_event,
)

def _get_redis():
    """Lazy-import redis.asyncio to avoid startup failure if Redis is missing."""
    try:
        import redis.asyncio as aioredis
        return aioredis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    except ImportError:
        return None

_redis_client = None

def _redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = _get_redis()
    return _redis_client

_SLIDING_WINDOW_LUA = """
local key     = KEYS[1]
local now_ms  = tonumber(ARGV[1])
local win_ms  = tonumber(ARGV[2])
local limit   = tonumber(ARGV[3])
local member  = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now_ms - win_ms)
local count = redis.call('ZCARD', key)
if count < limit then
  redis.call('ZADD', key, now_ms, member)
  redis.call('PEXPIRE', key, win_ms)
  return count + 1
end
return -1
"""

import secrets

async def _sliding_window_check(
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """
    Check and record a request against a Redis sliding window.

    Returns (allowed, retry_after_seconds).
    If Redis is unavailable, returns (True, 0) — fail open.
    """
    r = _redis()
    if r is None:
        return True, 0

    now_ms = int(time.time() * 1000)
    win_ms = window_seconds * 1000
    member = f"{now_ms}:{secrets.token_hex(6)}"
    redis_key = f"rl:sw:{key}"

    try:
        result = await r.eval(
            _SLIDING_WINDOW_LUA,
            1,
            redis_key,
            str(now_ms),
            str(win_ms),
            str(limit),
            member,
        )
        if result == -1:
            
            oldest = await r.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                oldest_ms = oldest[0][1]
                retry_sec = max(1, int((oldest_ms + win_ms - now_ms) / 1000))
            else:
                retry_sec = window_seconds
            return False, retry_sec
        return True, 0
    except Exception as exc:
        logger.warning("[rate_limit] Redis error, failing open: %s", exc)
        return True, 0

"""
Lockout tiers (based on cumulative failure count stored in Redis):
  5  failures → 15 min ban
  10 failures → 1 hr ban
  20 failures → 24 hr ban

Failure counter resets after 24 h of no activity.
"""

async def _get_lockout_ttl(lock_key: str) -> int:
    """Returns seconds remaining in lockout, or 0 if not locked."""
    r = _redis()
    if r is None:
        return 0
    try:
        ttl = await r.ttl(f"rl:lock:{lock_key}")
        return max(0, ttl)
    except Exception:
        return 0

async def _record_failure(lock_key: str) -> None:
    """Increment failure counter and apply lockout if threshold is reached."""
    r = _redis()
    if r is None:
        return
    fail_key = f"rl:fails:{lock_key}"
    try:
        fails = await r.incr(fail_key)
        await r.expire(fail_key, 86_400)  

        lock_ttl = 0
        if fails >= 20:
            lock_ttl = 86_400   
        elif fails >= 10:
            lock_ttl = 3_600    
        elif fails >= 5:
            lock_ttl = 900      

        if lock_ttl:
            
            await r.set(f"rl:lock:{lock_key}", "1", ex=lock_ttl, nx=True)
    except Exception as exc:
        logger.warning("[rate_limit] Could not record failure for %s: %s", lock_key, exc)

async def _clear_failures(lock_key: str) -> None:
    """Clear failure counters on successful authentication."""
    r = _redis()
    if r is None:
        return
    try:
        await r.delete(f"rl:fails:{lock_key}", f"rl:lock:{lock_key}")
    except Exception:
        pass

def _ip_lock_key(ip: str) -> str:
    return f"ip:{_hash_for_log(ip)}"

def _email_lock_key(email: str) -> str:
    return f"email:{_hash_for_log(email.lower())}"

async def record_login_failure(request: Request, email: Optional[str] = None) -> None:
    """
    Call from a login route handler when credentials are INVALID.

    Increments failure counters for:
      - The client IP
      - The target email (if provided), keyed by its hash

    After enough failures, progressive lockouts are applied.
    """
    ip = _extract_client_ip(request)
    await _record_failure(_ip_lock_key(ip))
    if email:
        await _record_failure(_email_lock_key(email))
        log_security_event(request, "login_failure", {"email_hash": _hash_for_log(email.lower())})
    else:
        log_security_event(request, "login_failure")

async def record_login_success(request: Request, email: str) -> None:
    """
    Call from a login route handler when credentials are VALID.

    Clears failure counters for IP and email so a legitimate user
    isn't locked out after occasional mistakes.
    """
    ip = _extract_client_ip(request)
    await _clear_failures(_ip_lock_key(ip))
    await _clear_failures(_email_lock_key(email))

class RateLimitCheck:
    """
    FastAPI dependency for endpoint-level rate limiting.

    Applies:
      1. IP sliding window (max_per_ip / window_seconds)
      2. Optional per-email sliding window for auth endpoints
      3. Progressive lockout checks

    Parameters
    ----------
    prefix : str
        Unique identifier for this limit (used as Redis key prefix).
    max_per_ip : int
        Maximum requests per IP per window.
    window_seconds : int
        Window duration in seconds.
    check_email_lockout : bool
        If True, also check email-based lockout (set request.state.login_email first).

    Example
    -------
        @router.post("/auth/login")
        async def login(
            body: LoginBody,
            request: Request,
            _: None = Depends(RateLimitCheck("auth:login", max_per_ip=5, window_seconds=900, check_email_lockout=True)),
        ):
            ...
    """

    def __init__(
        self,
        prefix: str,
        max_per_ip: int,
        window_seconds: int,
        check_email_lockout: bool = False,
    ):
        self.prefix = prefix
        self.max_per_ip = max_per_ip
        self.window_seconds = window_seconds
        self.check_email_lockout = check_email_lockout

    async def __call__(self, request: Request) -> None:
        ip = _extract_client_ip(request)
        ip_key = _ip_lock_key(ip)

        ip_lock_ttl = await _get_lockout_ttl(ip_key)
        if ip_lock_ttl > 0:
            log_security_event(request, "ip_locked_out", {"prefix": self.prefix})
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many failed attempts from this location.",
                    "retry_after": ip_lock_ttl,
                },
                headers={"Retry-After": str(ip_lock_ttl)},
            )

        allowed, retry_sec = await _sliding_window_check(
            f"{self.prefix}:ip:{_hash_for_log(ip)}",
            self.max_per_ip,
            self.window_seconds,
        )
        if not allowed:
            log_security_event(request, "rate_limit_exceeded_ip", {"prefix": self.prefix})
            await _record_failure(ip_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many requests. Please wait before trying again.",
                    "retry_after": retry_sec,
                },
                headers={"Retry-After": str(retry_sec)},
            )

        if self.check_email_lockout:
            email: str = getattr(request.state, "login_email", "") or ""
            if email:
                email_key = _email_lock_key(email)
                email_lock_ttl = await _get_lockout_ttl(email_key)
                if email_lock_ttl > 0:
                    log_security_event(request, "account_locked_out", {"prefix": self.prefix})
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "This account is temporarily locked. Reset your password or try again later.",
                            "retry_after": email_lock_ttl,
                        },
                        headers={"Retry-After": str(email_lock_ttl)},
                    )

                allowed_email, retry_sec_email = await _sliding_window_check(
                    f"{self.prefix}:email:{_hash_for_log(email.lower())}",
                    3,
                    self.window_seconds,
                )
                if not allowed_email:
                    log_security_event(request, "rate_limit_exceeded_email", {"prefix": self.prefix})
                    await _record_failure(email_key)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Too many attempts for this account.",
                            "retry_after": retry_sec_email,
                        },
                        headers={"Retry-After": str(retry_sec_email)},
                    )
