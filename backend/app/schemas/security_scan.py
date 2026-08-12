import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SecurityScanRequest(BaseModel):
    domain: str = Field(min_length=3, max_length=255)


class SecurityScanPublic(BaseModel):
    id: uuid.UUID
    domain: str
    score: int
    ssl_info: dict | None
    dns_records: dict | None
    whois_info: dict | None
    headers_info: dict | None
    reputation_info: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
