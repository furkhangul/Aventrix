import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_jwt,
    create_refresh_token,
    decode_jwt,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.totp import (
    generate_backup_codes,
    generate_totp_secret,
    get_provisioning_uri,
    verify_totp_code,
)
from app.integrations.email.factory import get_email_provider
from app.models.enums import UserRole
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session_repository import get_session_by_refresh_hash
from app.repositories.user_repository import get_user_by_email, get_user_by_id
from app.services.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
    InvalidTwoFactorCodeError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
)

settings = get_settings()

EMAIL_VERIFICATION_EXPIRY = timedelta(hours=24)
PASSWORD_RESET_EXPIRY = timedelta(hours=1)
TWO_FA_PENDING_EXPIRY = timedelta(minutes=5)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < _utcnow()


# --- Registration / verification -------------------------------------------------


async def register_user(db: AsyncSession, *, email: str, password: str, full_name: str | None) -> User:
    if await get_user_by_email(db, email):
        raise EmailAlreadyRegisteredError()

    verification_token = generate_opaque_token()
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.USER,
        email_verification_token_hash=hash_token(verification_token),
        email_verification_expires_at=_utcnow() + EMAIL_VERIFICATION_EXPIRY,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    verify_url = f"{settings.frontend_base_url}/verify-email?token={verification_token}"
    await get_email_provider().send(
        to=user.email,
        subject=f"Verify your {settings.app_name} account",
        body_text=f"Welcome to {settings.app_name}! Verify your email:\n\n{verify_url}",
    )
    return user


async def resend_verification_email(db: AsyncSession, user: User) -> None:
    if user.is_email_verified:
        return
    verification_token = generate_opaque_token()
    user.email_verification_token_hash = hash_token(verification_token)
    user.email_verification_expires_at = _utcnow() + EMAIL_VERIFICATION_EXPIRY
    await db.commit()

    verify_url = f"{settings.frontend_base_url}/verify-email?token={verification_token}"
    await get_email_provider().send(
        to=user.email,
        subject=f"Verify your {settings.app_name} account",
        body_text=f"Verify your email:\n\n{verify_url}",
    )


async def verify_email(db: AsyncSession, token: str) -> User:
    token_hash = hash_token(token)
    result = await db.execute(select(User).where(User.email_verification_token_hash == token_hash))
    user = result.scalar_one_or_none()
    if not user or _is_expired(user.email_verification_expires_at):
        raise InvalidOrExpiredTokenError()

    user.is_email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    await db.commit()
    return user


# --- Login / sessions --------------------------------------------------------------


async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise AccountInactiveError()
    return user


def create_two_factor_pending_token(user: User) -> str:
    return create_jwt(
        subject=str(user.id),
        token_type="two_factor_pending",
        expires_delta=TWO_FA_PENDING_EXPIRY,
    )


def resolve_two_factor_pending_user_id(pending_token: str) -> uuid.UUID:
    payload = decode_jwt(pending_token)
    if not payload or payload.get("type") != "two_factor_pending":
        raise InvalidOrExpiredTokenError()
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise InvalidOrExpiredTokenError()


async def create_session_and_tokens(
    db: AsyncSession, *, user: User, user_agent: str | None, ip_address: str | None
) -> tuple[str, str, UserSession]:
    session = UserSession(
        user_id=user.id,
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip_address,
        expires_at=_utcnow() + timedelta(days=settings.refresh_token_expire_days),
        refresh_token_hash="pending",  # replaced below once we know the session id
    )
    db.add(session)
    await db.flush()  # assigns session.id

    refresh_token = create_refresh_token(user_id=str(user.id), session_id=str(session.id))
    session.refresh_token_hash = hash_token(refresh_token)
    access_token = create_access_token(user_id=str(user.id), role=user.role)

    await db.commit()
    await db.refresh(session)
    return access_token, refresh_token, session


async def rotate_refresh_token(
    db: AsyncSession, *, raw_refresh_token: str, user_agent: str | None, ip_address: str | None
) -> tuple[str, str, UserSession]:
    payload = decode_jwt(raw_refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise InvalidOrExpiredTokenError()

    session = await get_session_by_refresh_hash(db, hash_token(raw_refresh_token))
    if not session or not session.is_active or _is_expired(session.expires_at):
        raise InvalidOrExpiredTokenError()
    if str(session.id) != payload.get("sid"):
        raise InvalidOrExpiredTokenError()

    user = await get_user_by_id(db, session.user_id)
    if not user or not user.is_active:
        raise InvalidOrExpiredTokenError()

    # Rotation: revoke the old session/token, issue a brand new one.
    session.revoked_at = _utcnow()
    await db.flush()

    return await create_session_and_tokens(db, user=user, user_agent=user_agent, ip_address=ip_address)


async def revoke_session_by_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    session = await get_session_by_refresh_hash(db, hash_token(raw_refresh_token))
    if session and session.is_active:
        session.revoked_at = _utcnow()
        await db.commit()


# --- Password reset / change -------------------------------------------------------


async def request_password_reset(db: AsyncSession, email: str) -> None:
    user = await get_user_by_email(db, email)
    if not user:
        # Do not reveal whether the account exists.
        return
    reset_token = generate_opaque_token()
    user.password_reset_token_hash = hash_token(reset_token)
    user.password_reset_expires_at = _utcnow() + PASSWORD_RESET_EXPIRY
    await db.commit()

    reset_url = f"{settings.frontend_base_url}/reset-password?token={reset_token}"
    await get_email_provider().send(
        to=user.email,
        subject=f"Reset your {settings.app_name} password",
        body_text=f"Reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.",
    )


async def reset_password(db: AsyncSession, *, token: str, new_password: str) -> User:
    token_hash = hash_token(token)
    result = await db.execute(select(User).where(User.password_reset_token_hash == token_hash))
    user = result.scalar_one_or_none()
    if not user or _is_expired(user.password_reset_expires_at):
        raise InvalidOrExpiredTokenError()

    user.hashed_password = hash_password(new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    await db.commit()
    return user


async def change_password(db: AsyncSession, *, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentialsError()
    user.hashed_password = hash_password(new_password)
    await db.commit()


# --- Two-factor authentication ------------------------------------------------------


async def setup_two_factor(db: AsyncSession, user: User) -> tuple[str, str, list[str]]:
    if user.is_2fa_enabled:
        raise TwoFactorAlreadyEnabledError()

    secret = generate_totp_secret()
    backup_codes = generate_backup_codes()
    user.totp_secret = secret
    user.backup_codes_hashed = [hash_token(code) for code in backup_codes]
    await db.commit()

    return secret, get_provisioning_uri(secret, user.email), backup_codes


async def confirm_two_factor(db: AsyncSession, user: User, code: str) -> None:
    if not user.totp_secret or not verify_totp_code(user.totp_secret, code):
        raise InvalidTwoFactorCodeError()
    user.is_2fa_enabled = True
    await db.commit()


async def disable_two_factor(db: AsyncSession, user: User, *, password: str, code: str) -> None:
    if not user.is_2fa_enabled:
        raise TwoFactorNotEnabledError()
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    if not _verify_totp_or_backup(user, code):
        raise InvalidTwoFactorCodeError()

    user.is_2fa_enabled = False
    user.totp_secret = None
    user.backup_codes_hashed = None
    await db.commit()


async def regenerate_backup_codes(db: AsyncSession, user: User) -> list[str]:
    if not user.is_2fa_enabled:
        raise TwoFactorNotEnabledError()
    backup_codes = generate_backup_codes()
    user.backup_codes_hashed = [hash_token(code) for code in backup_codes]
    await db.commit()
    return backup_codes


def _verify_totp_or_backup(user: User, code: str) -> bool:
    if user.totp_secret and verify_totp_code(user.totp_secret, code):
        return True
    if user.backup_codes_hashed:
        code_hash = hash_token(code.strip())
        if code_hash in user.backup_codes_hashed:
            user.backup_codes_hashed = [h for h in user.backup_codes_hashed if h != code_hash]
            return True
    return False


async def verify_login_two_factor_code(db: AsyncSession, user: User, code: str) -> None:
    if not _verify_totp_or_backup(user, code):
        raise InvalidTwoFactorCodeError()
    await db.commit()  # persists backup-code consumption, if one was used


# --- Account deletion ---------------------------------------------------------------


async def delete_account(db: AsyncSession, *, user: User, password: str) -> None:
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    await db.delete(user)
    await db.commit()
