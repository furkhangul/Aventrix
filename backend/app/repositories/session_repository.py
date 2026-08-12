import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import UserSession


async def get_session_by_id(db: AsyncSession, session_id: uuid.UUID) -> UserSession | None:
    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    return result.scalar_one_or_none()


async def get_session_by_refresh_hash(db: AsyncSession, refresh_token_hash: str) -> UserSession | None:
    result = await db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == refresh_token_hash)
    )
    return result.scalar_one_or_none()


async def list_active_sessions_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[UserSession]:
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_used_at.desc())
    )
    return list(result.scalars().all())
