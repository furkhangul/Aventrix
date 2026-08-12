import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.link import Link


async def get_link_by_id(db: AsyncSession, link_id: uuid.UUID) -> Link | None:
    result = await db.execute(select(Link).where(Link.id == link_id))
    return result.scalar_one_or_none()


async def get_owned_link(db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID) -> Link | None:
    """IDOR-safe lookup: only returns the link if this user owns it."""
    result = await db.execute(
        select(Link)
        .where(Link.id == link_id, Link.user_id == user_id)
        .options(selectinload(Link.campaign))
    )
    return result.scalar_one_or_none()


async def get_link_by_short_code(db: AsyncSession, short_code: str) -> Link | None:
    # Eager-loads campaign: is_link_usable() checks link.campaign.status, and
    # a lazy relationship access would fail on this async session.
    result = await db.execute(
        select(Link).where(Link.short_code == short_code).options(selectinload(Link.campaign))
    )
    return result.scalar_one_or_none()


async def short_code_exists(db: AsyncSession, short_code: str) -> bool:
    result = await db.execute(select(Link.id).where(Link.short_code == short_code))
    return result.scalar_one_or_none() is not None
