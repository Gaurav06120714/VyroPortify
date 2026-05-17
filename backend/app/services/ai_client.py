"""Shared OpenRouter AI client.

Replaces Anthropic SDK — uses OpenRouter's OpenAI-compatible REST API.
Free models: meta-llama/llama-3.1-8b-instruct:free
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "google/gemma-4-31b-it:free"


def call_ai(
    prompt: str,
    system: str = "",
    model: str = FREE_MODEL,
    max_tokens: int = 2048,
) -> str:
    """Call OpenRouter and return the response text.

    Args:
        prompt: The user message.
        system: Optional system prompt.
        model: OpenRouter model string.
        max_tokens: Max tokens to generate.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        RuntimeError: On API error or empty response.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.FRONTEND_URL,
        "X-Title": "PortifyAI",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(OPENROUTER_BASE, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as exc:
        logger.error("OpenRouter HTTP error %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(f"AI API error: {exc.response.status_code}") from exc
    except Exception as exc:
        logger.error("OpenRouter call failed: %s", exc)
        raise RuntimeError(f"AI call failed: {exc}") from exc
