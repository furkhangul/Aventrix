import uuid
from datetime import datetime, timezone

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.core.security import decode_jwt, hash_token
from app.models.enums import ROLE_HIERARCHY, ApiKeyTier, UserRole
from app.models.user import User
from app.repositories.api_key_repository import get_api_key_by_hash
from app.utils.network import get_client_ip

# Distinguishes an API key from a JWT before attempting to decode either —
# JWTs are base64url segments joined by dots and never start with this.
API_KEY_PREFIX = "fw_live_"

_TIER_LIMIT_SETTING = {
    ApiKeyTier.FREE: "rate_limit_api_key_free_per_day",
    ApiKeyTier.PRO: "rate_limit_api_key_pro_per_day",
    ApiKeyTier.BUSINESS: "rate_limit_api_key_business_per_day",
}

__all__ = [
    "get_token_from_request",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_feature",
    "get_client_ip",
]

settings = get_settings()


async def get_token_from_request(
    request: Request,
    access_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return access_token


async def _authenticate_via_api_key(token: str, db: AsyncSession) -> User:
    """
    Alternate credential path: API keys (spec section 21) authenticate
    against the same routes a JWT would, gated by a per-tier daily request
    limit instead of the short-lived-session model JWTs use.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    api_key = await get_api_key_by_hash(db, hash_token(token))
    if not api_key or not api_key.is_active:
        raise credentials_error
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise credentials_error

    tier = ApiKeyTier(api_key.tier)
    daily_limit = getattr(settings, _TIER_LIMIT_SETTING[tier])
    allowed, retry_after = await check_rate_limit(f"apikey:{api_key.id}", daily_limit, window_seconds=86_400)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API key daily rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_error
    return user


async def get_current_user(
    token: str | None = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    if token.startswith(API_KEY_PREFIX):
        return await _authenticate_via_api_key(token, db)

    payload = decode_jwt(token)
    if not payload or payload.get("type") != "access":
        raise credentials_error

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_error

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_error
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return user


def require_role(minimum_role: UserRole):
    """
    Server-side RBAC gate. Every protected route that needs more than
    "logged in" must depend on this — hiding buttons in the UI is not
    access control.
    """

    async def _dependency(user: User = Depends(get_current_active_user)) -> User:
        user_rank = ROLE_HIERARCHY.index(UserRole(user.role))
        required_rank = ROLE_HIERARCHY.index(minimum_role)
        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return _dependency


def require_feature(flag_name: str):
    """
    Gates a router behind a feature flag (spec section 69). Missing/unset
    integration keys never crash the app (see the mock-provider factories);
    this only covers the coarser "this module isn't turned on at all" case.
    """

    async def _dependency() -> None:
        if not getattr(settings, flag_name, True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="This feature is not enabled"
            )

    return _dependency
