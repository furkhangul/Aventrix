import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import WebhookDeliveryStatus
from app.models.webhook import Webhook, WebhookDelivery
from app.repositories.webhook_repository import (
    get_active_webhooks_for_event,
    get_due_retryable_deliveries,
    get_owned_webhook,
    get_webhook_by_id,
)
from app.schemas.webhook import WebhookCreateRequest, WebhookUpdateRequest
from app.services import notification_service
from app.services.exceptions import InvalidUrlError, NotFoundError
from app.utils.pagination import paginate
from app.utils.safe_fetch import UnsafeUrlError, validate_url_for_fetch

settings = get_settings()

# Backoff schedule in minutes, indexed by (attempt_count - 1); the last
# entry repeats implicitly since we cap the index. attempt_count reaching
# settings.webhook_max_retry_attempts stops retries permanently.
RETRY_BACKOFF_MINUTES = [2, 10, 30, 120, 360]


def _generate_secret() -> str:
    return f"whsec_{secrets.token_urlsafe(32)}"


def sign_payload(secret: str, payload_json: str) -> str:
    digest = hmac.new(secret.encode(), payload_json.encode(), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def create_webhook(db: AsyncSession, *, user_id: uuid.UUID, data: WebhookCreateRequest) -> Webhook:
    try:
        await validate_url_for_fetch(data.url)
    except UnsafeUrlError as exc:
        raise InvalidUrlError(str(exc))

    webhook = Webhook(
        user_id=user_id,
        url=data.url,
        description=data.description,
        secret=_generate_secret(),
        events=[e.value for e in data.events],
        is_active=True,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


async def list_webhooks(
    db: AsyncSession, *, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[Webhook], int]:
    stmt = select(Webhook).where(Webhook.user_id == user_id).order_by(Webhook.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_webhook_for_user(db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID) -> Webhook:
    webhook = await get_owned_webhook(db, user_id=user_id, webhook_id=webhook_id)
    if not webhook:
        raise NotFoundError()
    return webhook


async def update_webhook(
    db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID, data: WebhookUpdateRequest
) -> Webhook:
    webhook = await get_webhook_for_user(db, user_id=user_id, webhook_id=webhook_id)
    if data.url is not None:
        try:
            await validate_url_for_fetch(data.url)
        except UnsafeUrlError as exc:
            raise InvalidUrlError(str(exc))
        webhook.url = data.url
    if data.description is not None:
        webhook.description = data.description
    if data.events is not None:
        webhook.events = [e.value for e in data.events]
    if data.is_active is not None:
        webhook.is_active = data.is_active
    await db.commit()
    await db.refresh(webhook)
    return webhook


async def delete_webhook(db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID) -> None:
    webhook = await get_webhook_for_user(db, user_id=user_id, webhook_id=webhook_id)
    await db.delete(webhook)
    await db.commit()


async def list_deliveries(
    db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[WebhookDelivery], int]:
    await get_webhook_for_user(db, user_id=user_id, webhook_id=webhook_id)  # ownership check
    stmt = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
    )
    return await paginate(db, stmt, page=page, page_size=page_size)


async def _attempt_delivery(db: AsyncSession, *, webhook: Webhook, delivery: WebhookDelivery) -> None:
    payload_json = json.dumps(delivery.payload, separators=(",", ":"), sort_keys=True)
    delivery.attempt_count += 1
    success = False

    try:
        # Re-validated at delivery time too, not just at creation — the
        # target's DNS could have changed since the webhook was configured.
        await validate_url_for_fetch(webhook.url)
        async with httpx.AsyncClient(timeout=settings.webhook_delivery_timeout_seconds) as client:
            response = await client.post(
                webhook.url,
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Event": delivery.event_type,
                    "X-Webhook-Id": str(delivery.id),
                    "X-Webhook-Signature": sign_payload(webhook.secret, payload_json),
                },
                follow_redirects=False,
            )
        delivery.response_status_code = response.status_code
        success = 200 <= response.status_code < 300
    except (UnsafeUrlError, httpx.HTTPError):
        delivery.response_status_code = None

    if success:
        delivery.status = WebhookDeliveryStatus.SUCCESS
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.next_retry_at = None
        await db.commit()
        return

    delivery.status = WebhookDeliveryStatus.FAILED
    if delivery.attempt_count >= settings.webhook_max_retry_attempts:
        delivery.next_retry_at = None
        await db.commit()
        await notification_service.notify_webhook_delivery_failed(
            db,
            user_id=webhook.user_id,
            webhook_id=webhook.id,
            url=webhook.url,
            event_type=delivery.event_type,
        )
    else:
        backoff_index = min(delivery.attempt_count - 1, len(RETRY_BACKOFF_MINUTES) - 1)
        delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(
            minutes=RETRY_BACKOFF_MINUTES[backoff_index]
        )
        await db.commit()


async def deliver_webhook_event(db: AsyncSession, *, user_id: uuid.UUID, event_type: str, payload: dict) -> None:
    """Called by the worker consumer for a queued event: fans out to every matching active webhook."""
    webhooks = await get_active_webhooks_for_event(db, user_id=user_id, event_type=event_type)
    for webhook in webhooks:
        delivery = WebhookDelivery(webhook_id=webhook.id, event_type=event_type, payload=payload)
        db.add(delivery)
        await db.flush()
        await _attempt_delivery(db, webhook=webhook, delivery=delivery)


async def retry_due_deliveries(db: AsyncSession) -> None:
    """Called by the periodic sweep: retries deliveries whose backoff window has elapsed."""
    now = datetime.now(timezone.utc)
    for delivery in await get_due_retryable_deliveries(db, now=now):
        webhook = await get_webhook_by_id(db, delivery.webhook_id)
        if not webhook or not webhook.is_active:
            delivery.next_retry_at = None
            await db.commit()
            continue
        await _attempt_delivery(db, webhook=webhook, delivery=delivery)


async def test_webhook(db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID) -> WebhookDelivery:
    webhook = await get_webhook_for_user(db, user_id=user_id, webhook_id=webhook_id)
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type="webhook.test",
        payload={"message": "This is a test delivery from FurOfTheWeak.", "webhook_id": str(webhook.id)},
    )
    db.add(delivery)
    await db.flush()
    await _attempt_delivery(db, webhook=webhook, delivery=delivery)
    await db.refresh(delivery)
    return delivery
