import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DevicePublic(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    is_active: bool
    last_seen_at: datetime | None
    paired_at: datetime
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class PairingCodeCreatedResponse(BaseModel):
    code: str
    expires_at: datetime
    qr_code_data_url: str


class DevicePairingExchangeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32)
    device_name: str = Field(min_length=1, max_length=150)
    device_fingerprint: str = Field(min_length=1, max_length=255)
    platform: str = Field(default="android", max_length=20)


class IceServer(BaseModel):
    urls: str
    username: str | None = None
    credential: str | None = None


class DevicePairingExchangeResponse(BaseModel):
    device: DevicePublic
    device_secret: str


class DeviceSessionTokenRequest(BaseModel):
    session_id: uuid.UUID


class DevicePendingSessionResponse(BaseModel):
    session_id: uuid.UUID | None


class DeviceWsTicketResponse(BaseModel):
    ticket: str
    ice_servers: list[IceServer]
    expires_in: int


class DeviceSessionStartResponse(BaseModel):
    session_id: uuid.UUID
    web_ticket: str
    ice_servers: list[IceServer]
    expires_at: datetime


class DeviceSessionPublic(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    ended_reason: str | None
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
