import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repository import get_session_by_id, list_active_sessions_for_user
from app.services.exceptions import NotFoundError, PermissionDeniedError


async def list_sessions(db: AsyncSession, user: User) -> list[UserSession]:
    return await list_active_sessions_for_user(db, user.id)


async def revoke_session(db: AsyncSession, *, user: User, session_id: uuid.UUID) -> None:
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError()
    if session.user_id != user.id:
        # IDOR guard: users may only revoke their own sessions.
        raise PermissionDeniedError()
    session.revoked_at = datetime.now(timezone.utc)
    await db.commit()


async def revoke_all_sessions(db: AsyncSession, user_id: uuid.UUID, *, except_session_id: uuid.UUID | None = None) -> None:
    """Used after a password change/reset to force re-authentication everywhere else."""
    sessions = await list_active_sessions_for_user(db, user_id)
    now = datetime.now(timezone.utc)
    for session in sessions:
        if except_session_id and session.id == except_session_id:
            continue
        session.revoked_at = now
    await db.commit()
