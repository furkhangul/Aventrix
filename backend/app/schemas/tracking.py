from pydantic import BaseModel, Field


class LinkMetaResponse(BaseModel):
    needs_password: bool
    needs_consent: bool


class ResolveLinkRequest(BaseModel):
    password: str | None = Field(default=None, max_length=128)
    consent: bool = True


class ResolveLinkResponse(BaseModel):
    target_url: str
