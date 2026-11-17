"""Typed access to the Apaleo MCP connector tools, with caching and concurrency limits."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from env.app import env as app_env
from mistralai.client import Mistral
from utils.mistral import caller_mistral_client

logger = logging.getLogger(__name__)

_CALL_TIMEOUT_SECONDS = 60
_MAX_PARALLEL_CALLS = 4
_RATE_LIMIT_RETRIES = 4
_RETRY_BASE_SECONDS = 2.0

_semaphore = asyncio.Semaphore(_MAX_PARALLEL_CALLS)
_cache: dict[tuple[str, str, str], tuple[float, Any]] = {}
_cache_lock = asyncio.Lock()


class ApaleoError(RuntimeError):
    """A connector call failed."""

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(f"Apaleo tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name


def connector_name() -> str:
    return app_env.apaleo_connector


def _client() -> Mistral:
    return caller_mistral_client()


def _extract_payload(result: Any) -> Any:
    """Pull the JSON payload out of an MCP tool result."""
    structured = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
    if structured:
        return structured
    text = "".join(item.text for item in (result.content or []) if hasattr(item, "text"))
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def call_tool(tool_name: str, arguments: dict | None = None, *, ttl_seconds: float = 0) -> Any:
    """Call one Apaleo connector tool and return its parsed `data` payload.

    Results are cached in-process for `ttl_seconds` when positive.
    """
    arguments = arguments or {}
    cache_key = (connector_name(), tool_name, json.dumps(arguments, sort_keys=True, default=str))

    if ttl_seconds > 0:
        async with _cache_lock:
            hit = _cache.get(cache_key)
            if hit and hit[0] > time.monotonic():
                return hit[1]

    async with _semaphore:
        for attempt in range(_RATE_LIMIT_RETRIES + 1):
            try:
                result = await _client().beta.connectors.call_tool_async(
                    connector_id_or_name=connector_name(),
                    tool_name=tool_name,
                    arguments=arguments,
                )
                break
            except Exception as error:
                message = str(error)
                if "429" in message and attempt < _RATE_LIMIT_RETRIES:
                    await asyncio.sleep(_RETRY_BASE_SECONDS * (2**attempt))
                    continue
                raise ApaleoError(tool_name, message) from error

    payload = _extract_payload(result)
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]

    if ttl_seconds > 0:
        async with _cache_lock:
            _cache[cache_key] = (time.monotonic() + ttl_seconds, payload)
    return payload


async def cached_call(tool_name: str, arguments: dict | None = None, *, ttl_seconds: float = 300) -> Any:
    return await call_tool(tool_name, arguments, ttl_seconds=ttl_seconds)


def invalidate_cache() -> None:
    _cache.clear()
