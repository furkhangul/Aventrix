import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationPublic,
    UpdateNotificationPreferencesRequest,
)
from app.services import notification_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total, unread_count = await notification_service.list_notifications(
        db, user_id=user.id, page=page, page_size=page_size, unread_only=unread_only
    )
    return NotificationListResponse(
        items=[NotificationPublic.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    preferences = await notification_service.get_preferences(db, user_id=user.id)
    return NotificationPreferencesResponse(preferences=preferences)


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    body: UpdateNotificationPreferencesRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    preferences = await notification_service.update_preferences(db, user_id=user.id, preferences=body.preferences)
    return NotificationPreferencesResponse(preferences=preferences)


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        notification = await notification_service.mark_read(db, user_id=user.id, notification_id=notification_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    await notification_service.mark_all_read(db, user_id=user.id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await notification_service.delete_notification(db, user_id=user.id, notification_id=notification_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
