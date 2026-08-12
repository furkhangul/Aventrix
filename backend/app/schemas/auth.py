import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.utils.validation import normalize_email, validate_password_strength

PasswordField = Annotated[str, Field(min_length=10, max_length=128)]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: PasswordField
    full_name: str | None = Field(default=None, max_length=150)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    avatar_url: str | None
    role: UserRole
    is_active: bool
    is_email_verified: bool
    is_2fa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    requires_2fa: bool = False
    two_factor_pending_token: str | None = None
    user: UserPublic | None = None


class TwoFactorVerifyLoginRequest(BaseModel):
    two_factor_pending_token: str
    code: str = Field(min_length=6, max_length=10)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: PasswordField

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: PasswordField

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class VerifyEmailRequest(BaseModel):
    token: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)


class SessionPublic(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    backup_codes: list[str]


class TwoFactorConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=10)


class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=10)


class AccountDeleteRequest(BaseModel):
    password: str


class MessageResponse(BaseModel):
    message: str
