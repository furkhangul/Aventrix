import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user, require_feature
from app.core import audit_actions
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.models.enums import AuditResult
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.security_scan import SecurityScanPublic, SecurityScanRequest
from app.services import security_center_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import InvalidUrlError, NotFoundError

router = APIRouter(
    prefix="/security-center", tags=["security-center"], dependencies=[Depends(require_feature("enable_domain_analyzer"))]
)


@router.post(
    "/scan",
    response_model=SecurityScanPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(10, window_seconds=60, scope="security-scan"))],
)
async def run_scan(
    body: SecurityScanRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scan = await security_center_service.run_scan(db, user_id=user.id, domain=body.domain)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    await write_audit_log(
        db,
        action=audit_actions.SECURITY_SCAN_RUN,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="security_scan",
        resource_id=str(scan.id),
        ip_address=get_client_ip(request),
        metadata={"domain": scan.domain, "score": scan.score},
    )
    return scan


@router.get("/scans", response_model=PaginatedResponse[SecurityScanPublic])
async def list_scans(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await security_center_service.list_scans(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/scans/{scan_id}", response_model=SecurityScanPublic)
async def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await security_center_service.get_scan_for_user(db, user_id=user.id, scan_id=scan_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
