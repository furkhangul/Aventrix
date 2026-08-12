import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import WebhookEventType
from app.utils.url_validation import validate_target_url


class WebhookCreateRequest(BaseModel):
    url: str = Field(max_length=2048)
    description: str | None = Field(default=None, max_length=500)
    events: list[WebhookEventType] = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        try:
            return validate_target_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class WebhookUpdateRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=500)
    events: list[WebhookEventType] | None = Field(default=None, min_length=1)
    is_active: bool | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            return validate_target_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class WebhookPublic(BaseModel):
    id: uuid.UUID
    url: str
    description: str | None
    events: list[str]
    is_active: bool
    secret_preview: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreatedResponse(WebhookPublic):
    secret: str


class WebhookDeliveryPublic(BaseModel):
    id: uuid.UUID
    event_type: str
    status: str
    response_status_code: int | None
    attempt_count: int
    next_retry_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
