import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import CampaignStatus
from app.utils.short_code import is_reserved, is_valid_alias_format
from app.utils.url_validation import validate_target_url


class UTMParams(BaseModel):
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)
    utm_term: str | None = Field(default=None, max_length=100)
    utm_content: str | None = Field(default=None, max_length=100)

    def to_dict(self) -> dict | None:
        data = {k: v for k, v in self.model_dump().items() if v}
        return data or None


class LinkCreateRequest(BaseModel):
    target_url: str = Field(max_length=2048)
    campaign_id: uuid.UUID | None = None
    custom_alias: str | None = Field(default=None, min_length=3, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    expires_at: datetime | None = None
    password: str | None = Field(default=None, min_length=4, max_length=128)
    requires_consent: bool = True
    utm: UTMParams = Field(default_factory=UTMParams)

    @field_validator("target_url")
    @classmethod
    def _validate_target(cls, v: str) -> str:
        try:
            return validate_target_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))

    @field_validator("custom_alias")
    @classmethod
    def _validate_alias(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not is_valid_alias_format(v):
            raise ValueError(
                "Alias must be 3-64 characters: letters, numbers, hyphens, underscores only"
            )
        if is_reserved(v):
            raise ValueError("This alias is reserved and cannot be used")
        return v

    @model_validator(mode="after")
    def _validate_expiry(self) -> "LinkCreateRequest":
        if self.expires_at is not None:
            expires_at = self.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("Expiration must be in the future")
        return self


class LinkUpdateRequest(BaseModel):
    campaign_id: uuid.UUID | None = None
    target_url: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    expires_at: datetime | None = None
    is_active: bool | None = None
    requires_consent: bool | None = None

    @field_validator("target_url")
    @classmethod
    def _validate_target(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            return validate_target_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class LinkSetPasswordRequest(BaseModel):
    password: str | None = Field(default=None, min_length=4, max_length=128)


class LinkPublic(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID | None
    campaign_name: str | None
    campaign_status: CampaignStatus | None
    short_code: str
    short_url: str
    target_url: str
    description: str | None
    tags: list[str] | None
    is_active: bool
    expires_at: datetime | None
    is_password_protected: bool
    requires_consent: bool
    utm_params: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LinkWithStats(LinkPublic):
    total_visits: int = 0
    unique_visitors: int = 0


class VisitPublic(BaseModel):
    id: uuid.UUID
    created_at: datetime
    consent_given: bool
    ip_address: str | None
    country: str | None
    country_code: str | None
    region: str | None
    city: str | None
    district: str | None
    timezone: str | None
    latitude: float | None
    longitude: float | None
    isp: str | None
    asn: str | None
    organization: str | None
    hostname: str | None
    is_mobile: bool | None
    device_type: str | None
    browser: str | None
    browser_version: str | None
    os: str | None
    os_version: str | None
    language: str | None
    referrer: str | None
    is_vpn: str
    is_proxy: str
    is_tor: str
    is_hosting: str
    bot_confidence: str
    utm_snapshot: dict | None
    visit_number: int | None = None
    is_returning_visitor: bool = False

    model_config = {"from_attributes": True}
