"""
Minimal async-native task queue on Redis lists.

Spec section 7 allows either Celery or "a modern async task system" for the
queue. This app is async end-to-end (FastAPI + asyncpg); a synchronous
Celery/kombu client called from request handlers turned out to hang
indefinitely in this environment whenever the broker was unreachable (its
own configured socket timeouts were not honored, and the stuck worker
thread outlives any asyncio-level timeout wrapped around it). redis.asyncio
— already used successfully by the rate limiter, with a proven fast,
graceful fallback — does not have that problem, so background jobs are
built on it directly instead.
"""

import asyncio
import json
import logging
import uuid

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger("furoftheweak.workers.queue")
settings = get_settings()

ENRICH_VISIT_QUEUE = "furoftheweak:queue:enrich_visit"
WEBHOOK_DELIVERY_QUEUE = "furoftheweak:queue:webhook_delivery"
ENQUEUE_TIMEOUT_SECONDS = 1.0

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def enqueue_visit_enrichment(visit_id: uuid.UUID, raw_ip: str) -> None:
    """
    Fire-and-forget: pushes an enrichment job onto a Redis list consumed by
    the worker process (app/workers/runner.py). Never raises and never
    blocks the caller for more than ENQUEUE_TIMEOUT_SECONDS — if Redis is
    unreachable, the visit is simply left unenriched rather than the
    redirect waiting on it.
    """
    payload = json.dumps({"visit_id": str(visit_id), "raw_ip": raw_ip})
    try:
        client = get_redis_client()
        await asyncio.wait_for(client.rpush(ENRICH_VISIT_QUEUE, payload), timeout=ENQUEUE_TIMEOUT_SECONDS)
    except Exception:
        logger.warning("enrich_visit_enqueue_failed", exc_info=True)


async def enqueue_webhook_event(user_id: uuid.UUID, event_type: str, payload: dict) -> None:
    """
    Fire-and-forget: pushes a webhook-event job onto a Redis list consumed by
    the worker process. The worker resolves which of this user's webhooks
    are subscribed to the event and delivers to each — this call never
    blocks the caller (link/campaign/visit creation) for more than
    ENQUEUE_TIMEOUT_SECONDS, matching enqueue_visit_enrichment's contract.
    """
    message = json.dumps({"user_id": str(user_id), "event_type": event_type, "payload": payload})
    try:
        client = get_redis_client()
        await asyncio.wait_for(client.rpush(WEBHOOK_DELIVERY_QUEUE, message), timeout=ENQUEUE_TIMEOUT_SECONDS)
    except Exception:
        logger.warning("webhook_event_enqueue_failed", exc_info=True)
