"""Unit tests for ai_client cache + failover (v1.2.2)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services import ai_client


def _store():
    """In-memory cache backed by a dict."""
    d: dict[str, str] = {}

    def get(k):
        return d.get(k)

    def set_(k, v, _ttl):
        d[k] = v

    return d, get, set_


class TestCallAi:
    def test_cache_hit_short_circuits(self):
        d, g, s = _store()
        d[ai_client._cache_key("p", "", ai_client.FREE_MODEL, 100)] = "cached"

        out = ai_client.call_ai(
            "p", max_tokens=100, _cache_get_fn=g, _cache_set_fn=s
        )
        assert out == "cached"

    def test_anthropic_preferred_when_available(self):
        d, g, s = _store()
        with patch.object(ai_client, "_call_anthropic") as a, \
             patch.object(ai_client, "_call_openrouter") as o:
            a.return_value = ai_client._Result("from-claude", "anthropic", "x")
            out = ai_client.call_ai(
                "hello", max_tokens=10, _cache_get_fn=g, _cache_set_fn=s
            )
        assert out == "from-claude"
        assert o.called is False
        # Result is cached.
        assert any(v == "from-claude" for v in d.values())

    def test_falls_back_to_openrouter_on_anthropic_failure(self):
        d, g, s = _store()
        with patch.object(ai_client, "_call_anthropic", side_effect=RuntimeError("boom")), \
             patch.object(ai_client, "_call_openrouter") as o:
            o.return_value = ai_client._Result("from-openrouter", "openrouter", "y")
            out = ai_client.call_ai(
                "hello", max_tokens=10, _cache_get_fn=g, _cache_set_fn=s
            )
        assert out == "from-openrouter"

    def test_raises_when_all_providers_fail(self):
        d, g, s = _store()
        with patch.object(ai_client, "_call_anthropic", side_effect=RuntimeError("a")), \
             patch.object(ai_client, "_call_openrouter", side_effect=RuntimeError("b")):
            with pytest.raises(RuntimeError, match="All AI providers failed"):
                ai_client.call_ai(
                    "hello", max_tokens=10, _cache_get_fn=g, _cache_set_fn=s
                )

    def test_use_cache_false_bypasses_cache_read_and_write(self):
        d, g, s = _store()
        # Pre-seed; with use_cache=False this must NOT be returned.
        d[ai_client._cache_key("p", "", ai_client.FREE_MODEL, 10)] = "stale"

        with patch.object(ai_client, "_call_anthropic") as a:
            a.return_value = ai_client._Result("fresh", "anthropic", "x")
            out = ai_client.call_ai(
                "p", max_tokens=10, use_cache=False,
                _cache_get_fn=g, _cache_set_fn=s,
            )
        assert out == "fresh"
        # Cache wasn't overwritten with the fresh value.
        assert d[ai_client._cache_key("p", "", ai_client.FREE_MODEL, 10)] == "stale"
