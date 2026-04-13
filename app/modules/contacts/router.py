"""Contacts API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.modules.contacts import schemas, service

router = APIRouter()


@router.post("", response_model=schemas.ContactResponse, status_code=201)
async def create_contact(
    body: schemas.ContactCreate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_contact(
        db, tenant.id, **body.model_dump(exclude_unset=True),
    )


@router.get("")
async def list_contacts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    contacts, total = await service.list_contacts(db, tenant.id, page, size)
    return {"items": contacts, "total": total, "page": page, "size": size}


@router.get("/{contact_id}", response_model=schemas.ContactResponse)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_contact(db, tenant.id, contact_id)


@router.put("/{contact_id}", response_model=schemas.ContactResponse)
async def update_contact(
    contact_id: UUID,
    body: schemas.ContactUpdate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_contact(
        db, tenant.id, contact_id, **body.model_dump(exclude_unset=True),
    )
