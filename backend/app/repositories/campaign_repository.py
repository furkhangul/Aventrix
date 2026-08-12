import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign


async def get_owned_campaign(db: AsyncSession, *, user_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign | None:
    """IDOR-safe lookup: only returns the campaign if this user owns it."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    return result.scalar_one_or_none()
