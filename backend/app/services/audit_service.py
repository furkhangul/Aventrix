import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditResult


async def write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    result: AuditResult,
    user_id: uuid.UUID | None = None,
    user_email_snapshot: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        user_email_snapshot=user_email_snapshot,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        result=result,
        log_metadata=metadata,
    )
    db.add(entry)
    if commit:
        await db.commit()
    else:
        await db.flush()
    return entry
