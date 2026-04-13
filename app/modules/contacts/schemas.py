"""Contact Pydantic schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class ContactCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    vip: bool = False
    default_project_id: UUID | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    vip: bool | None = None
    default_project_id: UUID | None = None


class ContactResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    email: str | None
    phone: str | None
    company: str | None
    vip: bool
    default_project_id: UUID | None
    created_at: str | None
    updated_at: str | None

    model_config = {"from_attributes": True}
