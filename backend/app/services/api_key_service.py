import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.api_key import ApiKey
from app.repositories.api_key_repository import get_owned_api_key
from app.schemas.api_key import ApiKeyCreateRequest
from app.services.exceptions import NotFoundError
from app.utils.pagination import paginate

# Distinguishes an API key from a JWT at auth time (see app/api/deps.py) —
# JWTs never start with this, so the two credential types never collide.
KEY_PREFIX = "fw_live_"
KEY_PREFIX_DISPLAY_LENGTH = len(KEY_PREFIX) + 8


def _generate_raw_key() -> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"


async def create_api_key(db: AsyncSession, *, user_id: uuid.UUID, data: ApiKeyCreateRequest) -> tuple[ApiKey, str]:
    raw_key = _generate_raw_key()
    api_key = ApiKey(
        user_id=user_id,
        name=data.name,
        key_hash=hash_token(raw_key),
        key_prefix=raw_key[:KEY_PREFIX_DISPLAY_LENGTH],
        tier=data.tier,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw_key


async def list_api_keys(db: AsyncSession, *, user_id: uuid.UUID, page: int, page_size: int) -> tuple[list[ApiKey], int]:
    stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_api_key_for_user(db: AsyncSession, *, user_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey:
    api_key = await get_owned_api_key(db, user_id=user_id, key_id=key_id)
    if not api_key:
        raise NotFoundError()
    return api_key


async def revoke_api_key(db: AsyncSession, *, user_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey:
    api_key = await get_api_key_for_user(db, user_id=user_id, key_id=key_id)
    api_key.is_active = False
    api_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def rotate_api_key(db: AsyncSession, *, user_id: uuid.UUID, key_id: uuid.UUID) -> tuple[ApiKey, str]:
    """Revokes the existing key and issues a fresh one with the same name/tier."""
    old_key = await get_api_key_for_user(db, user_id=user_id, key_id=key_id)
    old_key.is_active = False
    old_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return await create_api_key(db, user_id=user_id, data=ApiKeyCreateRequest(name=old_key.name, tier=old_key.tier))
