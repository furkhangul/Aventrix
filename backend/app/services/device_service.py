import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import constant_time_compare, create_jwt, decode_jwt, generate_opaque_token, hash_token
from app.models.device import Device, DevicePairingCode, DeviceSession
from app.models.enums import DevicePairingStatus, DeviceSessionStatus
from app.repositories.device_repository import (
    get_device_by_id,
    get_latest_pending_session_for_device,
    get_owned_device,
    get_owned_session,
    get_pairing_code_by_hash,
    get_session_by_id,
    get_stale_pairing_codes,
    get_stale_sessions,
)
from app.schemas.device import IceServer
from app.services import device_signaling_service, turn_credential_service
from app.services.exceptions import InvalidCredentialsError, InvalidOrExpiredTokenError, NotFoundError
from app.utils.pagination import paginate
from app.utils.short_code import generate_short_code

settings = get_settings()

PAIRING_CODE_LENGTH = 8


def as_aware_utc(dt: datetime) -> datetime:
    """
    SQLite (used by the test suite; see models/types.py's dialect-portable
    types) drops tzinfo on round-trip even for DateTime(timezone=True)
    columns — Postgres (production) does not. Normalize to UTC before
    comparing against datetime.now(timezone.utc) so the same comparison
    code is correct on both.
    """
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def create_pairing_code(db: AsyncSession, *, user_id: uuid.UUID) -> tuple[DevicePairingCode, str]:
    code = generate_short_code(PAIRING_CODE_LENGTH)
    now = datetime.now(timezone.utc)
    pairing = DevicePairingCode(
        user_id=user_id,
        code_hash=hash_token(code),
        status=DevicePairingStatus.PENDING,
        expires_at=now + timedelta(seconds=settings.device_pairing_code_ttl_seconds),
    )
    db.add(pairing)
    await db.commit()
    await db.refresh(pairing)
    return pairing, code


async def exchange_pairing_code(
    db: AsyncSession, *, code: str, device_name: str, device_fingerprint: str, platform: str
) -> tuple[Device, str]:
    """Consumes a pairing code and registers the device. Raises InvalidOrExpiredTokenError on a bad/expired code."""
    pairing = await get_pairing_code_by_hash(db, hash_token(code))
    now = datetime.now(timezone.utc)
    if not pairing or as_aware_utc(pairing.expires_at) < now:
        raise InvalidOrExpiredTokenError("Pairing code is invalid or expired")

    device_secret = generate_opaque_token()
    device = Device(
        user_id=pairing.user_id,
        name=device_name,
        device_fingerprint=device_fingerprint,
        platform=platform or "android",
        is_active=True,
        device_secret_hash=hash_token(device_secret),
        paired_at=now,
    )
    db.add(device)
    await db.flush()

    pairing.status = DevicePairingStatus.CONSUMED
    pairing.consumed_at = now
    pairing.resulting_device_id = device.id

    await db.commit()
    await db.refresh(device)
    return device, device_secret


async def list_devices(db: AsyncSession, *, user_id: uuid.UUID, page: int, page_size: int):
    stmt = select(Device).where(Device.user_id == user_id).order_by(Device.paired_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_device_for_user(db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID) -> Device:
    device = await get_owned_device(db, user_id=user_id, device_id=device_id)
    if not device:
        raise NotFoundError()
    return device


async def rename_device(db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID, name: str) -> Device:
    device = await get_device_for_user(db, user_id=user_id, device_id=device_id)
    device.name = name
    await db.commit()
    await db.refresh(device)
    return device


async def revoke_device(db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID) -> Device:
    device = await get_device_for_user(db, user_id=user_id, device_id=device_id)
    device.is_active = False
    device.revoked_at = datetime.now(timezone.utc)

    result = await db.execute(
        select(DeviceSession).where(
            DeviceSession.device_id == device_id,
            DeviceSession.status.in_([DeviceSessionStatus.PENDING, DeviceSessionStatus.ACTIVE]),
        )
    )
    for session in result.scalars().all():
        session.status = DeviceSessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        session.ended_reason = "revoked"
        # Actively tear down any live WS relay rather than leaving media
        # flowing while the DB says revoked — best-effort, a session with
        # no connected peers simply has nothing listening on the channel.
        try:
            await device_signaling_service.publish_to_both(session.id, {"type": "bye", "data": {"reason": "revoked"}})
        except Exception:
            pass

    await db.commit()
    await db.refresh(device)
    return device


async def list_device_sessions(db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID, page: int, page_size: int):
    await get_device_for_user(db, user_id=user_id, device_id=device_id)  # ownership check
    stmt = select(DeviceSession).where(DeviceSession.device_id == device_id).order_by(DeviceSession.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def start_session(
    db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID
) -> tuple[DeviceSession, str, list[IceServer]]:
    device = await get_device_for_user(db, user_id=user_id, device_id=device_id)
    if not device.is_active:
        raise NotFoundError()

    now = datetime.now(timezone.utc)
    session = DeviceSession(
        device_id=device.id,
        user_id=user_id,
        status=DeviceSessionStatus.PENDING,
        expires_at=now + timedelta(seconds=settings.device_session_max_duration_seconds),
    )
    db.add(session)
    await db.flush()

    web_ticket = create_jwt(
        subject=str(user_id),
        token_type="device_ws",
        expires_delta=timedelta(seconds=settings.device_ws_ticket_ttl_seconds),
        extra_claims={"session_id": str(session.id), "role": "controller"},
    )
    session.web_ticket_jti = decode_jwt(web_ticket)["jti"]

    await db.commit()
    await db.refresh(session)

    ice_servers = turn_credential_service.generate_ice_servers(subject_id=user_id)
    return session, web_ticket, ice_servers


async def end_session(
    db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID, session_id: uuid.UUID, reason: str = "user_ended"
) -> DeviceSession:
    session = await get_owned_session(db, user_id=user_id, session_id=session_id)
    if not session or session.device_id != device_id:
        raise NotFoundError()

    session.status = DeviceSessionStatus.ENDED
    session.ended_at = datetime.now(timezone.utc)
    session.ended_reason = reason
    try:
        await device_signaling_service.publish_to_both(session.id, {"type": "bye", "data": {"reason": reason}})
    except Exception:
        pass

    await db.commit()
    await db.refresh(session)
    return session


async def issue_device_ticket(
    db: AsyncSession, *, device_id: uuid.UUID, device_secret: str, session_id: uuid.UUID
) -> tuple[str, list[IceServer]]:
    """
    Lets a paired device turn its persisted secret into a short-lived
    signaling ticket for a session the web/controller side already started.
    Authenticated by the device secret itself, not a user JWT — the phone
    has no browser session.
    """
    device = await get_device_by_id(db, device_id)
    if not device or not device.is_active:
        raise InvalidCredentialsError()
    if not constant_time_compare(device.device_secret_hash, hash_token(device_secret)):
        raise InvalidCredentialsError()

    session = await get_session_by_id(db, session_id)
    now = datetime.now(timezone.utc)
    if not session or session.device_id != device_id:
        raise NotFoundError()
    if as_aware_utc(session.expires_at) < now or session.status == DeviceSessionStatus.ENDED:
        raise InvalidOrExpiredTokenError("Session is no longer active")

    device_ticket = create_jwt(
        subject=str(device_id),
        token_type="device_ws",
        expires_delta=timedelta(seconds=settings.device_ws_ticket_ttl_seconds),
        extra_claims={"session_id": str(session_id), "role": "target"},
    )
    session.device_ticket_jti = decode_jwt(device_ticket)["jti"]
    device.last_seen_at = now
    await db.commit()

    ice_servers = turn_credential_service.generate_ice_servers(subject_id=device_id)
    return device_ticket, ice_servers


async def get_pending_session(db: AsyncSession, *, device_id: uuid.UUID, device_secret: str) -> uuid.UUID | None:
    """
    Lets a paired device discover a session the web/controller side already
    started, before it knows the session_id that issue_device_ticket()
    requires. Authenticated by the device secret itself, same as
    issue_device_ticket — the phone has no browser session.
    """
    device = await get_device_by_id(db, device_id)
    if not device or not device.is_active:
        raise InvalidCredentialsError()
    if not constant_time_compare(device.device_secret_hash, hash_token(device_secret)):
        raise InvalidCredentialsError()

    session = await get_latest_pending_session_for_device(db, device_id=device_id)
    if not session or as_aware_utc(session.expires_at) < datetime.now(timezone.utc):
        return None
    return session.id


async def validate_ws_ticket(ticket: str, *, expected_session_id: uuid.UUID) -> dict:
    """Decodes and validates a device_ws ticket for the signaling WS endpoint. Returns its claims or raises."""
    payload = decode_jwt(ticket)
    if not payload or payload.get("type") != "device_ws":
        raise InvalidOrExpiredTokenError("Invalid or expired signaling ticket")
    if payload.get("session_id") != str(expected_session_id):
        raise InvalidOrExpiredTokenError("Ticket does not match this session")
    if payload.get("role") not in ("controller", "target"):
        raise InvalidOrExpiredTokenError("Invalid ticket role")
    return payload


async def mark_session_active_on_connect(db: AsyncSession, *, session_id: uuid.UUID) -> None:
    """Best-effort: flips PENDING -> ACTIVE on the first peer to connect."""
    session = await get_session_by_id(db, session_id)
    if session and session.status == DeviceSessionStatus.PENDING:
        session.status = DeviceSessionStatus.ACTIVE
        session.started_at = datetime.now(timezone.utc)
        await db.commit()


async def mark_session_ended(db: AsyncSession, *, session_id: uuid.UUID, reason: str) -> None:
    session = await get_session_by_id(db, session_id)
    if session and session.status in (DeviceSessionStatus.PENDING, DeviceSessionStatus.ACTIVE):
        session.status = DeviceSessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        session.ended_reason = reason
        await db.commit()


async def sweep_stale_devices(db: AsyncSession) -> int:
    """
    Called by the worker's periodic sweep: expires sessions and pairing
    codes past their TTL that were never explicitly ended/consumed (e.g.
    an abandoned pairing attempt, or a crashed peer that never sent "bye").
    """
    now = datetime.now(timezone.utc)
    swept = 0

    for session in await get_stale_sessions(db, now=now):
        session.status = DeviceSessionStatus.EXPIRED
        session.ended_at = now
        session.ended_reason = "timeout"
        swept += 1

    for pairing in await get_stale_pairing_codes(db, now=now):
        pairing.status = DevicePairingStatus.EXPIRED
        swept += 1

    if swept:
        await db.commit()
    return swept
