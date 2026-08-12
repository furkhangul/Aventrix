import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email.factory import get_email_provider
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.repositories.notification_repository import count_unread, get_owned_notification
from app.repositories.user_repository import get_user_by_id
from app.services.exceptions import NotFoundError
from app.utils.pagination import paginate

# Default (English) copy for system-triggered notification types. Callers
# that already have a more specific message (e.g. naming the link/domain)
# pass their own title/message instead of relying on these.
NOTIFICATION_TITLES: dict[NotificationType, str] = {
    NotificationType.LINK_EXPIRED: "Link expired",
    NotificationType.LINK_FIRST_VISIT: "First visit received",
    NotificationType.WEBHOOK_DELIVERY_FAILED: "Webhook delivery failed",
    NotificationType.SECURITY_SCAN_WARNING: "Security warning",
    NotificationType.TEST: "Test notification",
}


def _type_value(type_: NotificationType | str) -> str:
    return type_.value if isinstance(type_, NotificationType) else type_


async def _maybe_send_email(db: AsyncSession, *, user_id: uuid.UUID, type_key: str, title: str, message: str) -> None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return
    prefs = user.notification_preferences or {}
    # A type absent from the preferences dict defaults to enabled.
    if prefs.get(type_key, True) is False:
        return
    await get_email_provider().send(
        to=user.email,
        subject=f"[FurOfTheWeak] {title}",
        body_text=message,
    )


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    type_: NotificationType | str,
    title: str | None = None,
    message: str,
    data: dict | None = None,
) -> Notification:
    type_key = _type_value(type_)
    if title is not None:
        resolved_title = title
    else:
        resolved_title = NOTIFICATION_TITLES.get(NotificationType(type_key), type_key)

    notification = Notification(
        user_id=user_id,
        type=type_key,
        title=resolved_title,
        message=message,
        data=data,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    await _maybe_send_email(db, user_id=user_id, type_key=type_key, title=resolved_title, message=message)
    return notification


async def list_notifications(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    page: int,
    page_size: int,
    unread_only: bool = False,
) -> tuple[list[Notification], int, int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc())
    items, total = await paginate(db, stmt, page=page, page_size=page_size)
    unread = await count_unread(db, user_id=user_id)
    return items, total, unread


async def mark_read(db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notification = await get_owned_notification(db, user_id=user_id, notification_id=notification_id)
    if not notification:
        raise NotFoundError()
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()


async def delete_notification(db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
    notification = await get_owned_notification(db, user_id=user_id, notification_id=notification_id)
    if not notification:
        raise NotFoundError()
    await db.delete(notification)
    await db.commit()


async def get_preferences(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError()
    return user.notification_preferences or {}


async def update_preferences(db: AsyncSession, *, user_id: uuid.UUID, preferences: dict) -> dict:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError()
    current = dict(user.notification_preferences or {})
    current.update(preferences)
    user.notification_preferences = current
    await db.commit()
    return current


async def notify_link_first_visit(db: AsyncSession, *, user_id: uuid.UUID, short_code: str, link_id: uuid.UUID) -> None:
    await create_notification(
        db,
        user_id=user_id,
        type_=NotificationType.LINK_FIRST_VISIT,
        message=f"Your link /t/{short_code} just received its first visit.",
        data={"link_id": str(link_id)},
    )


async def notify_link_expired(db: AsyncSession, *, user_id: uuid.UUID, short_code: str, link_id: uuid.UUID) -> None:
    await create_notification(
        db,
        user_id=user_id,
        type_=NotificationType.LINK_EXPIRED,
        message=f"Your link /t/{short_code} has expired and is no longer redirecting.",
        data={"link_id": str(link_id)},
    )


async def notify_webhook_delivery_failed(
    db: AsyncSession, *, user_id: uuid.UUID, webhook_id: uuid.UUID, url: str, event_type: str
) -> None:
    await create_notification(
        db,
        user_id=user_id,
        type_=NotificationType.WEBHOOK_DELIVERY_FAILED,
        message=f"Delivery of '{event_type}' to {url} failed after all retry attempts.",
        data={"webhook_id": str(webhook_id), "event_type": event_type},
    )


async def notify_security_scan_warning(
    db: AsyncSession, *, user_id: uuid.UUID, domain: str, score: int, scan_id: uuid.UUID
) -> None:
    await create_notification(
        db,
        user_id=user_id,
        type_=NotificationType.SECURITY_SCAN_WARNING,
        message=f"Security scan for {domain} scored {score}/100 — review the findings in Security Center.",
        data={"domain": domain, "score": score, "scan_id": str(scan_id)},
    )
