from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, max_length=16)
    recovery_code: str | None = Field(default=None, max_length=32)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    mfa_required: bool = False
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"


class TotpSetupOut(BaseModel):
    secret: str
    otpauth_url: str


class TotpVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=16)


class TotpVerifyOut(BaseModel):
    recovery_codes: list[str]


class TotpDisableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class TotpStatusOut(BaseModel):
    enabled: bool


class GoogleExchangeRequest(BaseModel):
    login_code: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class UserSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
