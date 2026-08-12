import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WebhookDeliveryStatus
from app.models.webhook import Webhook, WebhookDelivery


async def get_webhook_by_id(db: AsyncSession, webhook_id: uuid.UUID) -> Webhook | None:
    """Internal use only (worker context) — no ownership filter. Never expose over HTTP."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    return result.scalar_one_or_none()


async def get_owned_webhook(db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID) -> Webhook | None:
    """IDOR-safe lookup: only returns the webhook if this user owns it."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == user_id))
    return result.scalar_one_or_none()


async def get_active_webhooks_for_event(db: AsyncSession, *, user_id: uuid.UUID, event_type: str) -> list[Webhook]:
    result = await db.execute(
        select(Webhook).where(Webhook.user_id == user_id, Webhook.is_active.is_(True))
    )
    webhooks = result.scalars().all()
    return [w for w in webhooks if event_type in (w.events or [])]


async def get_delivery(db: AsyncSession, delivery_id: uuid.UUID) -> WebhookDelivery | None:
    result = await db.execute(select(WebhookDelivery).where(WebhookDelivery.id == delivery_id))
    return result.scalar_one_or_none()


async def get_due_retryable_deliveries(db: AsyncSession, *, now, limit: int = 100) -> list[WebhookDelivery]:
    result = await db.execute(
        select(WebhookDelivery)
        .where(
            WebhookDelivery.status == WebhookDeliveryStatus.FAILED,
            WebhookDelivery.next_retry_at.is_not(None),
            WebhookDelivery.next_retry_at <= now,
        )
        .limit(limit)
    )
    return list(result.scalars().all())
