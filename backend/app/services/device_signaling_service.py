"""
WebRTC signaling relay for the Devices module: shuttles SDP offer/answer and
ICE candidate JSON messages between exactly two WebSocket peers (a browser
"controller" and, eventually, an Android "target") that share a session id.

Built on Redis pub/sub rather than an in-process dict — the backend
container runs uvicorn with --reload in dev and `restart: unless-stopped`
in prod, either of which can drop in-memory relay state mid-session; Redis
is already a hard dependency (see workers/queue.py's identical
redis.asyncio usage) so this costs nothing extra. Only signaling JSON ever
passes through here — video/audio/input media flows peer-to-peer (or via
TURN) entirely outside this process, so the backend can never record it.
"""

import asyncio
import json
import logging
import uuid

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger("furoftheweak.services.device_signaling")
settings = get_settings()

REDIS_CALL_TIMEOUT_SECONDS = 2.0
_redis_client: redis.Redis | None = None

# Exactly two roles share a session. Messages are addressed by publishing
# onto the *recipient's* channel — each peer subscribes only to its own —
# so a peer never receives an echo of the message it just sent itself
# (which a single shared channel would cause, since Redis pub/sub delivers
# to every subscriber including the publisher).
_OTHER_ROLE = {"controller": "target", "target": "controller"}


def _channel_name(session_id: uuid.UUID, listener_role: str) -> str:
    return f"furoftheweak:device_signal:{session_id}:{listener_role}"


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


async def publish_signal(session_id: uuid.UUID, sender_role: str, message: dict) -> None:
    recipient_role = _OTHER_ROLE[sender_role]
    client = _get_redis()
    await asyncio.wait_for(
        client.publish(_channel_name(session_id, recipient_role), json.dumps(message)),
        timeout=REDIS_CALL_TIMEOUT_SECONDS,
    )


async def publish_to_both(session_id: uuid.UUID, message: dict) -> None:
    """Used for out-of-band events (e.g. a revoke) with no single "sender" peer."""
    client = _get_redis()
    for role in ("controller", "target"):
        await asyncio.wait_for(
            client.publish(_channel_name(session_id, role), json.dumps(message)), timeout=REDIS_CALL_TIMEOUT_SECONDS
        )


class SignalRelay:
    """
    Async context manager wrapping a Redis pub/sub subscription to the
    channel this role listens on. Used by the WebSocket handler to receive
    whatever the *other* peer on the same session sends.
    """

    def __init__(self, session_id: uuid.UUID, role: str):
        self._session_id = session_id
        self._role = role
        self._client = _get_redis()
        self._pubsub = self._client.pubsub()

    async def __aenter__(self) -> "SignalRelay":
        await self._pubsub.subscribe(_channel_name(self._session_id, self._role))
        return self

    async def __aexit__(self, *exc_info) -> None:
        try:
            await self._pubsub.unsubscribe(_channel_name(self._session_id, self._role))
        finally:
            await self._pubsub.aclose()

    async def listen(self):
        async for raw in self._pubsub.listen():
            if raw.get("type") != "message":
                continue
            try:
                yield json.loads(raw["data"])
            except (TypeError, ValueError):
                logger.warning("device_signal_invalid_message", extra={"session_id": str(self._session_id)})
