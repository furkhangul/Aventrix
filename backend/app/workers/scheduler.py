"""
Minimal periodic-task loop for jobs with no external trigger: the webhook
retry sweep and the link-expiry notification sweep. The codebase has no
cron/scheduler dependency; this is the smallest addition that supports
"every N seconds, check for due work" without pulling one in.
"""

import asyncio
import logging
from typing import Awaitable, Callable

logger = logging.getLogger("aventrix.workers.scheduler")


async def run_periodic(interval_seconds: int, fn: Callable[[], Awaitable[None]]) -> None:
    while True:
        try:
            await fn()
        except Exception:
            logger.exception("periodic_task_failed", extra={"task": getattr(fn, "__name__", str(fn))})
        await asyncio.sleep(interval_seconds)
