import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user
from app.core import audit_actions
from app.core.database import get_db
from app.models.api_key import ApiKey
from app.models.enums import AuditResult
from app.models.user import User
from app.schemas.api_key import ApiKeyCreatedResponse, ApiKeyCreateRequest, ApiKeyPublic
from app.schemas.common import PaginatedResponse
from app.services import api_key_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _to_created(api_key: ApiKey, raw_key: str) -> ApiKeyCreatedResponse:
    return ApiKeyCreatedResponse(**ApiKeyPublic.model_validate(api_key).model_dump(), api_key=raw_key)


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    api_key, raw_key = await api_key_service.create_api_key(db, user_id=user.id, data=body)
    await write_audit_log(
        db,
        action=audit_actions.API_KEY_CREATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="api_key",
        resource_id=str(api_key.id),
        ip_address=get_client_ip(request),
        metadata={"tier": api_key.tier},
    )
    return _to_created(api_key, raw_key)


@router.get("", response_model=PaginatedResponse[ApiKeyPublic])
async def list_api_keys(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await api_key_service.list_api_keys(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{key_id}/rotate", response_model=ApiKeyCreatedResponse)
async def rotate_api_key(
    key_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        api_key, raw_key = await api_key_service.rotate_api_key(db, user_id=user.id, key_id=key_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await write_audit_log(
        db,
        action=audit_actions.API_KEY_ROTATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="api_key",
        resource_id=str(api_key.id),
        ip_address=get_client_ip(request),
    )
    return _to_created(api_key, raw_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await api_key_service.revoke_api_key(db, user_id=user.id, key_id=key_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await write_audit_log(
        db,
        action=audit_actions.API_KEY_REVOKED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="api_key",
        resource_id=str(key_id),
        ip_address=get_client_ip(request),
    )
