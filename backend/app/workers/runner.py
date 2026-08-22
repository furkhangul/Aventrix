"""
Worker process entrypoint: consumes background jobs pushed by
app/workers/queue.py, plus runs the periodic sweep (webhook retries,
link-expiry notifications). Run via `python -m app.workers.runner` (see
worker/Dockerfile — this is the process the `worker` docker-compose service
runs).
"""

import asyncio
import json
import logging
import uuid

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.services.device_service import sweep_stale_devices
from app.services.ip_intelligence_service import enrich_visit
from app.services.link_service import sweep_expired_links
from app.services.webhook_service import deliver_webhook_event, retry_due_deliveries
from app.workers.queue import ENRICH_VISIT_QUEUE, WEBHOOK_DELIVERY_QUEUE
from app.workers.scheduler import run_periodic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aventrix.workers.runner")
settings = get_settings()

POLL_TIMEOUT_SECONDS = 5
RETRY_DELAY_SECONDS = 2


async def _process_enrichment_job(payload: str) -> None:
    try:
        data = json.loads(payload)
        visit_id = uuid.UUID(data["visit_id"])
        raw_ip = data["raw_ip"]
    except (ValueError, KeyError, TypeError) as exc:
        logger.error("invalid_enrichment_job", extra={"error": str(exc), "payload": payload})
        return

    async with AsyncSessionLocal() as db:
        try:
            await enrich_visit(db, visit_id, raw_ip)
            logger.info("visit_enriched", extra={"visit_id": str(visit_id)})
        except Exception:
            logger.exception("enrich_visit_failed", extra={"visit_id": str(visit_id)})


async def _process_webhook_job(payload: str) -> None:
    try:
        data = json.loads(payload)
        user_id = uuid.UUID(data["user_id"])
        event_type = data["event_type"]
        event_payload = data["payload"]
    except (ValueError, KeyError, TypeError) as exc:
        logger.error("invalid_webhook_job", extra={"error": str(exc), "payload": payload})
        return

    async with AsyncSessionLocal() as db:
        try:
            await deliver_webhook_event(db, user_id=user_id, event_type=event_type, payload=event_payload)
            logger.info("webhook_event_delivered", extra={"user_id": str(user_id), "event_type": event_type})
        except Exception:
            logger.exception("webhook_event_delivery_failed", extra={"user_id": str(user_id)})


async def _consume_queue(client: redis.Redis, queue_name: str, handler) -> None:
    logger.info("worker_queue_started", extra={"queue": queue_name})
    while True:
        try:
            result = await client.blpop([queue_name], timeout=POLL_TIMEOUT_SECONDS)
            if result is None:
                continue
            _, payload = result
            await handler(payload)
        except (redis.RedisError, ConnectionError, OSError) as exc:
            logger.warning("worker_redis_unavailable", extra={"queue": queue_name, "error": str(exc)})
            await asyncio.sleep(RETRY_DELAY_SECONDS)


async def _sweep_once() -> None:
    async with AsyncSessionLocal() as db:
        expired_count = await sweep_expired_links(db)
        if expired_count:
            logger.info("expired_links_swept", extra={"count": expired_count})
        await retry_due_deliveries(db)
        devices_swept = await sweep_stale_devices(db)
        if devices_swept:
            logger.info("stale_device_sessions_swept", extra={"count": devices_swept})


async def run_forever() -> None:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    await asyncio.gather(
        _consume_queue(client, ENRICH_VISIT_QUEUE, _process_enrichment_job),
        _consume_queue(client, WEBHOOK_DELIVERY_QUEUE, _process_webhook_job),
        run_periodic(settings.worker_sweep_interval_seconds, _sweep_once),
    )


if __name__ == "__main__":
    asyncio.run(run_forever())
