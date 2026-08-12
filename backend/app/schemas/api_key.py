import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ApiKeyTier


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    tier: ApiKeyTier = ApiKeyTier.FREE


class ApiKeyPublic(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    tier: ApiKeyTier
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyPublic):
    api_key: str
