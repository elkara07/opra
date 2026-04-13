"""SLA configuration service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.sla import SLAConfig
from app.models.tenant import Tenant
from app.models.ticket import Ticket
from app.modules.sla.engine import calculate_due_date


# Default SLA thresholds (minutes)
DEFAULT_SLA = {
    "P1": {"response": 15, "update": 60, "resolution": 240, "escalation": [30, 60, 120]},
    "P2": {"response": 30, "update": 120, "resolution": 480, "escalation": [60, 120, 240]},
    "P3": {"response": 60, "update": 480, "resolution": 1440, "escalation": [120, 480, 720]},
    "P4": {"response": 480, "update": 1440, "resolution": 5760, "escalation": [1440, 2880, 4320]},
}


async def get_sla_config(
    db: AsyncSession, tenant_id: UUID, priority: str, project_id: UUID | None = None,
) -> SLAConfig | None:
    """Find the best matching SLA config for a ticket.

    Priority: project-specific > tenant default > system default.
    """
    # Try project-specific first
    if project_id:
        result = await db.execute(
            select(SLAConfig).where(
                SLAConfig.tenant_id == tenant_id,
                SLAConfig.priority == priority,
                SLAConfig.project_id == project_id,
            )
        )
        config = result.scalar_one_or_none()
        if config:
            return config

    # Try tenant default
    result = await db.execute(
        select(SLAConfig).where(
            SLAConfig.tenant_id == tenant_id,
            SLAConfig.priority == priority,
            SLAConfig.is_default == True,
            SLAConfig.project_id == None,
        )
    )
    return result.scalar_one_or_none()


async def apply_sla_to_ticket(
    db: AsyncSession, ticket: Ticket, tenant: Tenant,
) -> Ticket:
    """Calculate and set SLA due dates on a ticket."""
    sla_config = await get_sla_config(
        db, ticket.tenant_id, ticket.priority, ticket.project_id,
    )

    if sla_config:
        response_min = sla_config.response_minutes
        resolution_min = sla_config.resolution_minutes
        ticket.sla_config_id = sla_config.id
    else:
        # Use defaults
        defaults = DEFAULT_SLA.get(ticket.priority, DEFAULT_SLA["P3"])
        response_min = defaults["response"]
        resolution_min = defaults["resolution"]

    bh = tenant.business_hours or {}
    holidays = tenant.holidays or []
    tz = tenant.timezone or "UTC"

    ticket.sla_response_due = calculate_due_date(
        ticket.created_at, response_min, bh, holidays, tz,
    )
    ticket.sla_resolution_due = calculate_due_date(
        ticket.created_at, resolution_min, bh, holidays, tz,
    )

    await db.flush()
    return ticket


async def create_sla_config(
    db: AsyncSession, tenant_id: UUID, **kwargs,
) -> SLAConfig:
    config = SLAConfig(tenant_id=tenant_id, **kwargs)
    db.add(config)
    await db.flush()
    return config


async def list_sla_configs(
    db: AsyncSession, tenant_id: UUID,
) -> list[SLAConfig]:
    result = await db.execute(
        select(SLAConfig).where(SLAConfig.tenant_id == tenant_id)
    )
    return list(result.scalars().all())
