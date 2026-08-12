import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def get_owned_notification(
    db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification | None:
    """IDOR-safe lookup: only returns the notification if this user owns it."""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def count_unread(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    )
    return result.scalar_one()
