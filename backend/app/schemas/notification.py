import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NotificationPublic(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    message: str
    data: dict | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationPublic]
    total: int
    page: int
    page_size: int
    unread_count: int


class NotificationPreferencesResponse(BaseModel):
    preferences: dict[str, bool]


class UpdateNotificationPreferencesRequest(BaseModel):
    preferences: dict[str, bool] = Field(default_factory=dict)
