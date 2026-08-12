import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user, require_feature
from app.core import audit_actions
from app.core.database import get_db
from app.models.enums import AuditResult
from app.models.user import User
from app.models.webhook import Webhook
from app.schemas.common import PaginatedResponse
from app.schemas.webhook import (
    WebhookCreatedResponse,
    WebhookCreateRequest,
    WebhookDeliveryPublic,
    WebhookPublic,
    WebhookUpdateRequest,
)
from app.services import webhook_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import InvalidUrlError, NotFoundError

router = APIRouter(
    prefix="/webhooks", tags=["webhooks"], dependencies=[Depends(require_feature("enable_webhook"))]
)


def _secret_preview(secret: str) -> str:
    return f"{secret[:10]}…"


def _to_public(webhook: Webhook) -> WebhookPublic:
    return WebhookPublic(
        id=webhook.id,
        url=webhook.url,
        description=webhook.description,
        events=webhook.events,
        is_active=webhook.is_active,
        secret_preview=_secret_preview(webhook.secret),
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


def _to_created(webhook: Webhook) -> WebhookCreatedResponse:
    return WebhookCreatedResponse(**_to_public(webhook).model_dump(), secret=webhook.secret)


@router.post("", response_model=WebhookCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    body: WebhookCreateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        webhook = await webhook_service.create_webhook(db, user_id=user.id, data=body)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    await write_audit_log(
        db,
        action=audit_actions.WEBHOOK_CREATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="webhook",
        resource_id=str(webhook.id),
        ip_address=get_client_ip(request),
    )
    return _to_created(webhook)


@router.get("", response_model=PaginatedResponse[WebhookPublic])
async def list_webhooks(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await webhook_service.list_webhooks(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(items=[_to_public(w) for w in items], total=total, page=page, page_size=page_size)


@router.patch("/{webhook_id}", response_model=WebhookPublic)
async def update_webhook(
    webhook_id: uuid.UUID,
    body: WebhookUpdateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        webhook = await webhook_service.update_webhook(db, user_id=user.id, webhook_id=webhook_id, data=body)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    await write_audit_log(
        db,
        action=audit_actions.WEBHOOK_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="webhook",
        resource_id=str(webhook_id),
        ip_address=get_client_ip(request),
    )
    return _to_public(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await webhook_service.delete_webhook(db, user_id=user.id, webhook_id=webhook_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    await write_audit_log(
        db,
        action=audit_actions.WEBHOOK_DELETED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="webhook",
        resource_id=str(webhook_id),
        ip_address=get_client_ip(request),
    )


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryPublic)
async def test_webhook(
    webhook_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        delivery = await webhook_service.test_webhook(db, user_id=user.id, webhook_id=webhook_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    await write_audit_log(
        db,
        action=audit_actions.WEBHOOK_TESTED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="webhook",
        resource_id=str(webhook_id),
        ip_address=get_client_ip(request),
    )
    return delivery


@router.get("/{webhook_id}/deliveries", response_model=PaginatedResponse[WebhookDeliveryPublic])
async def list_deliveries(
    webhook_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total = await webhook_service.list_deliveries(
            db, user_id=user.id, webhook_id=webhook_id, page=page, page_size=page_size
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return PaginatedResponse(
        items=[WebhookDeliveryPublic.model_validate(d) for d in items], total=total, page=page, page_size=page_size
    )
