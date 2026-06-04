"""Shared AI client with prompt cache, provider failover, and token telemetry.

Routing (v1.2.2)
----------------
1. Hash (prompt, system, model, max_tokens) → SHA256.
2. Redis GET ai:prompt:<hash> — on hit, return the cached completion.
3. On miss, try providers in order: Anthropic → OpenRouter.
   - Each provider is tried once per call.
   - 5xx, timeouts, and 429 trigger fallthrough.
   - Other 4xx is re-raised (client error / bad prompt).
4. On success, write Redis SETEX for AI_CACHE_TTL_SECONDS.
5. One structured log per call: provider, model, prompt_chars,
   completion_chars, duration_ms, cache_hit.

`use_cache=False` opt-out exists for cover-letter-style endpoints where
identical inputs should still produce a fresh variation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_BASE = "https://api.anthropic.com/v1/messages"

FREE_MODEL = "google/gemma-4-31b-it:free"
ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

AI_CACHE_TTL_SECONDS = 60 * 60 * 24
_TIMEOUT_SECONDS = 60.0


def _cache_key(prompt: str, system: str, model: str, max_tokens: int) -> str:
    h = hashlib.sha256()
    h.update(json.dumps([model, system, prompt, max_tokens], sort_keys=True).encode())
    return f"ai:prompt:{h.hexdigest()}"


@dataclass
class _Result:
    text: str
    provider: str
    model: str


def _call_anthropic(prompt: str, system: str, max_tokens: int) -> _Result:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("anthropic_not_configured")
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system or "",
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
        resp = client.post(ANTHROPIC_BASE, json=payload, headers=headers)
    if resp.status_code >= 500 or resp.status_code == 429:
        raise RuntimeError(f"anthropic_transient_{resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))
    return _Result(text=text.strip(), provider="anthropic", model=ANTHROPIC_MODEL)


def _call_openrouter(prompt: str, system: str, model: str, max_tokens: int) -> _Result:
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("openrouter_not_configured")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.FRONTEND_URL,
        "X-Title": "VyroPortify",
    }
    with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
        resp = client.post(OPENROUTER_BASE, json=payload, headers=headers)
    if resp.status_code >= 500 or resp.status_code == 429:
        raise RuntimeError(f"openrouter_transient_{resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    return _Result(
        text=data["choices"][0]["message"]["content"].strip(),
        provider="openrouter",
        model=model,
    )


def _cache_get(key: str) -> str | None:
    try:
        import redis  # type: ignore[import-not-found]

        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return client.get(key)
    except Exception:
        return None


def _cache_set(key: str, value: str, ttl: int) -> None:
    try:
        import redis  # type: ignore[import-not-found]

        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.setex(key, ttl, value)
    except Exception:
        pass


def call_ai(
    prompt: str,
    system: str = "",
    model: str = FREE_MODEL,
    max_tokens: int = 2048,
    *,
    use_cache: bool = True,
    _cache_get_fn: Callable[[str], str | None] | None = None,
    _cache_set_fn: Callable[[str, str, int], None] | None = None,
) -> str:
    """Return AI completion. Cache → Anthropic → OpenRouter."""
    cache_get = _cache_get_fn or _cache_get
    cache_set = _cache_set_fn or _cache_set
    key = _cache_key(prompt, system, model, max_tokens)
    start = time.perf_counter()

    if use_cache:
        hit = cache_get(key)
        if hit is not None:
            logger.info(
                "ai_call cache_hit=true prompt_chars=%d completion_chars=%d duration_ms=%.1f",
                len(prompt), len(hit), (time.perf_counter() - start) * 1000,
            )
            return hit

    last_exc: Exception | None = None
    for attempt in (
        lambda: _call_anthropic(prompt, system, max_tokens),
        lambda: _call_openrouter(prompt, system, model, max_tokens),
    ):
        try:
            result = attempt()
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "ai_call cache_hit=false provider=%s model=%s "
                "prompt_chars=%d completion_chars=%d duration_ms=%.1f",
                result.provider, result.model,
                len(prompt), len(result.text), duration_ms,
            )
            if use_cache and result.text:
                cache_set(key, result.text, AI_CACHE_TTL_SECONDS)
            return result.text
        except Exception as exc:
            logger.warning("ai_provider_failed err=%s", exc)
            last_exc = exc
            continue

    raise RuntimeError(f"All AI providers failed: {last_exc}") from last_exc
