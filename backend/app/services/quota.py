"""Per-user daily quota enforcement (v3.3.1 — DDoS hardening).

Rate limits cap requests-per-minute against a single IP. They don't stop a
small botnet from grinding through expensive AI calls slowly — each IP stays
under the threshold while collectively burning thousands of dollars of model
credits in a day.

This module adds a *per-account* daily counter, backed by Redis with a
TTL aligned to the next UTC midnight. The counter is plan-aware:

    free        →   5 AI builds / day,  10 cover letters / day
    pro         →  50 AI builds / day, 200 cover letters / day
    enterprise  → 500 AI builds / day, 2000 cover letters / day

Buckets exposed:
    "ai_build"      — POST /resume/build, /portfolio/generate
    "ai_enhance"    — cover-letter / suggest-skills / summary
    "bulk_export"   — ZIP downloads (heavy serialisation)
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status

from app.core.cache import cache
from app.core.enums import Plan
from app.security import CurrentUser

logger = logging.getLogger(__name__)

# bucket -> {plan: daily cap}
_LIMITS: dict[str, dict[str, int]] = {
    "ai_build": {Plan.FREE.value: 5, Plan.PRO.value: 50, Plan.ENTERPRISE.value: 500},
    "ai_enhance": {Plan.FREE.value: 10, Plan.PRO.value: 200, Plan.ENTERPRISE.value: 2000},
    "bulk_export": {Plan.FREE.value: 2, Plan.PRO.value: 20, Plan.ENTERPRISE.value: 200},
}


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60, int((midnight - now).total_seconds()))


def _quota_key(user_id, bucket: str) -> str:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"quota:{bucket}:{user_id}:{day}"


async def consume(user, bucket: str, amount: int = 1) -> int:
    """Increment the caller's bucket counter; raise 429 when the cap is exceeded.

    Returns the new counter value after the increment.
    """
    cap = _LIMITS.get(bucket, {}).get(user.plan, _LIMITS[bucket][Plan.FREE.value])
    key = _quota_key(user.id, bucket)
    try:
        client = cache.client
        pipe = client.pipeline()
        pipe.incrby(key, amount)
        pipe.expire(key, _seconds_until_utc_midnight())
        result = await pipe.execute()
        new_val = int(result[0])
    except Exception as exc:
        # Fail-open: a Redis outage shouldn't make every AI request 500.
        # The fixed slowapi rate limits remain in force as a fallback.
        logger.warning("quota.consume redis_unavailable bucket=%s err=%s", bucket, exc)
        return 0

    if new_val > cap:
        logger.info(
            "quota.exceeded user=%s plan=%s bucket=%s used=%d cap=%d",
            user.id, user.plan, bucket, new_val, cap,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily {bucket} quota exceeded ({cap}/day on {user.plan}). Upgrade or try again tomorrow.",
            headers={"Retry-After": str(_seconds_until_utc_midnight())},
        )
    return new_val


def require_quota(bucket: str, amount: int = 1):
    """FastAPI dependency factory — drop into any expensive route."""

    async def _dep(current_user: CurrentUser):
        await consume(current_user, bucket, amount=amount)
        return current_user

    return _dep
