import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CampaignStatus


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)


class CampaignUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    status: CampaignStatus | None = None


class CampaignPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: CampaignStatus
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignWithStats(CampaignPublic):
    link_count: int = 0
    total_visits: int = 0
    unique_visitors: int = 0
