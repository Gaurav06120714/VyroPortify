"""Redis cache helper.

Usage:
    from app.core.cache import cache

    # Store with TTL
    await cache.set("key", value, ttl=3600)

    # Retrieve
    data = await cache.get("key")

    # Delete
    await cache.delete("key")

    # Decorator (async functions only)
    @cache.cached(ttl=3600, key="portfolio:{slug}")
    async def get_portfolio(slug: str): ...
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Cache GET failed key=%s: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            await self.client.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as exc:
            logger.warning("Cache SET failed key=%s: %s", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception as exc:
            logger.warning("Cache DELETE failed key=%s: %s", key, exc)

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a glob pattern."""
        try:
            async for key in self.client.scan_iter(pattern):
                await self.client.delete(key)
        except Exception as exc:
            logger.warning("Cache DELETE pattern=%s failed: %s", pattern, exc)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

cache = RedisCache()

PORTFOLIO_PAGE_TTL = 3600       
TEMPLATE_LIST_TTL = 86400       
PORTFOLIO_STATUS_TTL = 10       
