"""SLA configuration API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.models.tenant import Tenant
from app.models.user import User
from app.modules.sla import service


router = APIRouter()


class SLAConfigCreate(BaseModel):
    name: str
    priority: str
    response_minutes: int
    update_minutes: int
    resolution_minutes: int
    escalation_thresholds: list[int] | None = None
    is_default: bool = False
    project_id: UUID | None = None


class SLAConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    priority: str
    response_minutes: int
    update_minutes: int
    resolution_minutes: int
    escalation_thresholds: list | None
    is_default: bool
    project_id: UUID | None

    model_config = {"from_attributes": True}


@router.post("", response_model=SLAConfigResponse, status_code=201)
async def create_sla_config(
    body: SLAConfigCreate,
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_sla_config(
        db, tenant.id, **body.model_dump(),
    )


@router.get("", response_model=list[SLAConfigResponse])
async def list_sla_configs(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_sla_configs(db, tenant.id)
