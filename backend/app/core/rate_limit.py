"""
Redis-backed fixed-window rate limiting, with an automatic in-memory
fallback so a single dev/test process still works without Redis running.
The in-memory fallback is per-process only — it is NOT safe for a
multi-instance production deployment, which is why it only engages when
Redis is actually unreachable (logged loudly) rather than being a config
toggle.
"""

import asyncio
import logging
import time
from collections import defaultdict

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.utils.network import get_client_ip

logger = logging.getLogger("aventrix.rate_limit")
settings = get_settings()

# A slow/unreachable Redis must degrade to the in-memory fallback in well
# under a second, never hang — redis-py's own socket_connect_timeout has
# proven unreliable enough on some platforms that it's also wrapped in an
# explicit asyncio timeout below rather than trusted alone.
REDIS_CALL_TIMEOUT_SECONDS = 1.0

_redis_client: redis.Redis | None = None
_memory_hits: dict[str, list[float]] = defaultdict(list)
_warned_fallback = False


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=REDIS_CALL_TIMEOUT_SECONDS,
            socket_timeout=REDIS_CALL_TIMEOUT_SECONDS,
        )
    return _redis_client


def _check_memory(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    now = time.time()
    window_start = now - window_seconds
    hits = _memory_hits[key]
    while hits and hits[0] < window_start:
        hits.pop(0)
    if len(hits) >= limit:
        retry_after = max(1, int(window_seconds - (now - hits[0])) + 1)
        return False, retry_after
    hits.append(now)
    return True, 0


async def _check_redis(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    client = _get_redis()
    redis_key = f"ratelimit:{key}"
    current = await client.incr(redis_key)
    if current == 1:
        await client.expire(redis_key, window_seconds)
    if current > limit:
        ttl = await client.ttl(redis_key)
        return False, ttl if ttl and ttl > 0 else window_seconds
    return True, 0


async def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
    """Returns (allowed, retry_after_seconds)."""
    global _warned_fallback
    try:
        return await asyncio.wait_for(
            _check_redis(key, limit, window_seconds), timeout=REDIS_CALL_TIMEOUT_SECONDS
        )
    except (redis.RedisError, ConnectionError, OSError, asyncio.TimeoutError):
        if not _warned_fallback:
            logger.warning(
                "Redis unreachable — falling back to in-memory rate limiting "
                "(per-process only, not safe for multi-instance production)."
            )
            _warned_fallback = True
        return _check_memory(key, limit, window_seconds)


def reset_rate_limits_for_testing() -> None:
    """Test-only helper: clears the in-memory fallback store between tests."""
    _memory_hits.clear()


def rate_limit(limit: int, window_seconds: int = 60, scope: str = "generic"):
    """FastAPI dependency factory: limits requests per client IP."""

    async def _dependency(request: Request) -> None:
        client_ip = get_client_ip(request)
        key = f"{scope}:{client_ip}"
        allowed, retry_after = await check_rate_limit(key, limit, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return _dependency
