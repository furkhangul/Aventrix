import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_scan import SecurityScan


async def get_owned_scan(db: AsyncSession, *, user_id: uuid.UUID, scan_id: uuid.UUID) -> SecurityScan | None:
    """IDOR-safe lookup: only returns the scan if this user owns it."""
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.id == scan_id, SecurityScan.user_id == user_id)
    )
    return result.scalar_one_or_none()
