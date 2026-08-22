"""
WebRTC signaling relay for the Devices module: shuttles SDP offer/answer and
ICE candidate JSON messages between exactly two WebSocket peers (a browser
"controller" and an Android "target") that share a session id.

Built on Redis rather than an in-process dict — the backend container runs
uvicorn with --reload in dev and `restart: unless-stopped` in prod, either
of which can drop in-memory relay state mid-session; Redis is already a hard
dependency (see workers/queue.py's identical redis.asyncio usage) so this
costs nothing extra. Only signaling JSON ever passes through here —
video/audio/input media flows peer-to-peer (or via TURN) entirely outside
this process, so the backend can never record it.

Delivery is pub/sub *with a fallback mailbox*. Plain pub/sub drops anything
published while the recipient is not subscribed, and the two peers of a
session join seconds apart by design (the phone discovers the session by
polling, then its owner has to accept the MediaProjection consent dialog).
That reliably lost the target's SDP offer and its first ICE candidates, and
the controller then sat on "waiting for device" forever with no error. So:
PUBLISH reports how many subscribers it reached, and a message that reached
nobody is pushed onto a short-lived per-recipient Redis list instead, which
the recipient drains the moment it subscribes.
"""

import asyncio
import json
import logging
import uuid

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger("aventrix.services.device_signaling")
settings = get_settings()

REDIS_CALL_TIMEOUT_SECONDS = 2.0

# How long an undelivered message waits for its peer. Comfortably longer
# than the phone's poll interval + consent dialog, far shorter than a
# session, so a stale mailbox can never leak into a later session.
MAILBOX_TTL_SECONDS = 300
MAILBOX_MAX_MESSAGES = 200

_redis_client: redis.Redis | None = None

# Exactly two roles share a session. Messages are addressed by publishing
# onto the *recipient's* channel — each peer subscribes only to its own —
# so a peer never receives an echo of the message it just sent itself
# (which a single shared channel would cause, since Redis pub/sub delivers
# to every subscriber including the publisher).
_OTHER_ROLE = {"controller": "target", "target": "controller"}


def other_role(role: str) -> str:
    return _OTHER_ROLE[role]


def _channel_name(session_id: uuid.UUID, listener_role: str) -> str:
    return f"aventrix:device_signal:{session_id}:{listener_role}"


def _mailbox_name(session_id: uuid.UUID, listener_role: str) -> str:
    return f"aventrix:device_signal_mailbox:{session_id}:{listener_role}"


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


async def _deliver(session_id: uuid.UUID, recipient_role: str, message: dict) -> None:
    """
    PUBLISH to the recipient's channel; if nobody was listening, queue it in
    that recipient's mailbox instead so it survives until they connect.
    """
    client = _get_redis()
    payload = json.dumps(message)
    receivers = await asyncio.wait_for(
        client.publish(_channel_name(session_id, recipient_role), payload),
        timeout=REDIS_CALL_TIMEOUT_SECONDS,
    )
    if receivers:
        return

    mailbox = _mailbox_name(session_id, recipient_role)
    pipe = client.pipeline()
    pipe.rpush(mailbox, payload)
    pipe.ltrim(mailbox, -MAILBOX_MAX_MESSAGES, -1)
    pipe.expire(mailbox, MAILBOX_TTL_SECONDS)
    await asyncio.wait_for(pipe.execute(), timeout=REDIS_CALL_TIMEOUT_SECONDS)
    logger.debug(
        "device_signal_buffered",
        extra={"session_id": str(session_id), "role": recipient_role, "type": message.get("type")},
    )


async def publish_signal(session_id: uuid.UUID, sender_role: str, message: dict) -> None:
    await _deliver(session_id, _OTHER_ROLE[sender_role], message)


async def publish_to_role(session_id: uuid.UUID, recipient_role: str, message: dict) -> None:
    """Addresses one specific role — used for peer presence events raised by the relay itself."""
    await _deliver(session_id, recipient_role, message)


async def publish_to_both(session_id: uuid.UUID, message: dict) -> None:
    """Used for out-of-band events (e.g. a revoke) with no single "sender" peer."""
    for role in ("controller", "target"):
        await _deliver(session_id, role, message)


async def clear_session(session_id: uuid.UUID) -> None:
    """Drops both mailboxes once a session is over, so nothing is replayed later."""
    client = _get_redis()
    try:
        await asyncio.wait_for(
            client.delete(_mailbox_name(session_id, "controller"), _mailbox_name(session_id, "target")),
            timeout=REDIS_CALL_TIMEOUT_SECONDS,
        )
    except Exception:  # pragma: no cover - best effort cleanup
        logger.warning("device_signal_mailbox_cleanup_failed", extra={"session_id": str(session_id)})


class SignalRelay:
    """
    Async context manager wrapping a Redis subscription to the channel this
    role listens on. Used by the WebSocket handler to receive whatever the
    *other* peer on the same session sends.

    listen() yields anything queued in this role's mailbox first, then
    switches to live pub/sub. Subscribing before draining is what makes that
    safe: a message published in between is delivered live (PUBLISH sees a
    subscriber, so it is never mailboxed), and one published before the
    subscribe lands in the mailbox and is drained here — no gap, no
    duplicate.
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

    async def _drain_mailbox(self):
        mailbox = _mailbox_name(self._session_id, self._role)
        while True:
            raw = await asyncio.wait_for(self._client.lpop(mailbox), timeout=REDIS_CALL_TIMEOUT_SECONDS)
            if raw is None:
                return
            try:
                yield json.loads(raw)
            except (TypeError, ValueError):
                logger.warning("device_signal_invalid_mailbox_message", extra={"session_id": str(self._session_id)})

    async def listen(self):
        async for message in self._drain_mailbox():
            yield message

        async for raw in self._pubsub.listen():
            if raw.get("type") != "message":
                continue
            try:
                yield json.loads(raw["data"])
            except (TypeError, ValueError):
                logger.warning("device_signal_invalid_message", extra={"session_id": str(self._session_id)})
