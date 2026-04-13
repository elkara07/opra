"""Escalation rules API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.models.escalation import EscalationRule
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


class EscalationRuleCreate(BaseModel):
    sla_config_id: UUID
    level: int
    threshold_minutes: int
    notify_team_id: UUID | None = None
    notify_user_id: UUID | None = None
    notification_channels: list[str] | None = None
    is_active: bool = True


class EscalationRuleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    sla_config_id: UUID
    level: int
    threshold_minutes: int
    notify_team_id: UUID | None
    notify_user_id: UUID | None
    notification_channels: list | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("", response_model=EscalationRuleResponse, status_code=201)
async def create_escalation_rule(
    body: EscalationRuleCreate,
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    rule = EscalationRule(tenant_id=tenant.id, **body.model_dump())
    db.add(rule)
    await db.flush()
    return rule


@router.get("", response_model=list[EscalationRuleResponse])
async def list_escalation_rules(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EscalationRule)
        .where(EscalationRule.tenant_id == tenant.id)
        .order_by(EscalationRule.level)
    )
    return list(result.scalars().all())
