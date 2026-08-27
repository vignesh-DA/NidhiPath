"""
Thin Groq chat wrapper.

Generation and intake extraction use Groq (`gpt-oss-120b`) when configured.
If the key is missing or the call fails, callers MUST fall back — Module 4
enhances the experience and never gates the critical path (AD-10).
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from app.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqUnavailable(RuntimeError):
    """Raised when Groq is not configured or the request fails."""


def groq_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.1,
    json_mode: bool = False,
    timeout: float = 30.0,
    max_tokens: int = 1024,
) -> str:
    """
    Synchronous Groq chat completion.

    Raises GroqUnavailable on missing key, HTTP error, or empty content.
    """
    if not settings.has_groq:
        raise GroqUnavailable("GROQ_API_KEY is not configured")

    payload: dict[str, Any] = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise GroqUnavailable(f"Groq request failed: {exc}") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GroqUnavailable("Groq returned an unexpected payload") from exc

    if not content or not str(content).strip():
        raise GroqUnavailable("Groq returned empty content")

    return str(content).strip()


def groq_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Chat completion that must return a JSON object."""
    raw = groq_chat(messages, temperature=temperature, json_mode=True, timeout=timeout)
    # Models sometimes wrap JSON in fences even with json_mode.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GroqUnavailable(f"Groq JSON parse failed: {exc}") from exc
    if not isinstance(parsed, dict):
        raise GroqUnavailable("Groq JSON was not an object")
    return parsed


def groq_available() -> bool:
    return settings.has_groq
