"""Auth Pydantic schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID | None
    email: str
    name: str
    role: str
    auth_source: str
    is_active: bool
    mfa_enabled: bool

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    tenant_name: str
    tenant_slug: str
    email: EmailStr
    name: str
    password: str


class RegisterResponse(BaseModel):
    tenant_id: UUID
    user_id: UUID
    access_token: str
    refresh_token: str


class MFAVerifyRequest(BaseModel):
    code: str
