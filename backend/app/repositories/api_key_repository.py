import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey


async def get_owned_api_key(db: AsyncSession, *, user_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey | None:
    """IDOR-safe lookup: only returns the key if this user owns it."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id))
    return result.scalar_one_or_none()


async def get_api_key_by_hash(db: AsyncSession, key_hash: str) -> ApiKey | None:
    """Internal use only (auth dependency) — looked up by hash, not scoped to a user."""
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    return result.scalar_one_or_none()
