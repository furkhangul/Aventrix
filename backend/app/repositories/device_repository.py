import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DevicePairingCode, DeviceSession
from app.models.enums import DevicePairingStatus, DeviceSessionStatus


async def get_owned_device(db: AsyncSession, *, user_id: uuid.UUID, device_id: uuid.UUID) -> Device | None:
    """IDOR-safe lookup: only returns the device if this user owns it."""
    result = await db.execute(select(Device).where(Device.id == device_id, Device.user_id == user_id))
    return result.scalar_one_or_none()


async def get_device_by_id(db: AsyncSession, device_id: uuid.UUID) -> Device | None:
    """Internal use only (WS/worker context) — no ownership filter. Never expose over HTTP."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    return result.scalar_one_or_none()


async def get_owned_session(
    db: AsyncSession, *, user_id: uuid.UUID, session_id: uuid.UUID
) -> DeviceSession | None:
    result = await db.execute(
        select(DeviceSession).where(DeviceSession.id == session_id, DeviceSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_session_by_id(db: AsyncSession, session_id: uuid.UUID) -> DeviceSession | None:
    """Internal use only (WS context, ticket already proved authorization) — no ownership filter."""
    result = await db.execute(select(DeviceSession).where(DeviceSession.id == session_id))
    return result.scalar_one_or_none()


async def get_pairing_code_by_hash(db: AsyncSession, code_hash: str) -> DevicePairingCode | None:
    result = await db.execute(
        select(DevicePairingCode).where(
            DevicePairingCode.code_hash == code_hash, DevicePairingCode.status == DevicePairingStatus.PENDING
        )
    )
    return result.scalar_one_or_none()


async def get_latest_pending_session_for_device(db: AsyncSession, *, device_id: uuid.UUID) -> DeviceSession | None:
    """Newest PENDING session for this device, if any — lets the device discover a
    session the controller started without already knowing its session_id."""
    result = await db.execute(
        select(DeviceSession)
        .where(DeviceSession.device_id == device_id, DeviceSession.status == DeviceSessionStatus.PENDING)
        .order_by(DeviceSession.created_at.desc())
    )
    return result.scalars().first()


async def get_stale_sessions(db: AsyncSession, *, now: datetime, limit: int = 200) -> list[DeviceSession]:
    result = await db.execute(
        select(DeviceSession)
        .where(
            DeviceSession.status.in_([DeviceSessionStatus.PENDING, DeviceSessionStatus.ACTIVE]),
            DeviceSession.expires_at <= now,
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_stale_pairing_codes(db: AsyncSession, *, now: datetime, limit: int = 200) -> list[DevicePairingCode]:
    result = await db.execute(
        select(DevicePairingCode)
        .where(DevicePairingCode.status == DevicePairingStatus.PENDING, DevicePairingCode.expires_at <= now)
        .limit(limit)
    )
    return list(result.scalars().all())
