"""Reporting API endpoints: SLA compliance, ticket volume, agent performance."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.models.call_record import CallRecord
from app.models.ticket import Ticket, TicketEvent
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


@router.get("/sla-compliance")
async def sla_compliance(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """SLA compliance summary: met vs breached per priority."""
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            Ticket.priority,
            func.count(Ticket.id).label("total"),
            func.count(case((Ticket.sla_breached == True, 1))).label("breached"),
            func.count(case((Ticket.sla_responded_at != None, 1))).label("responded"),
        )
        .where(Ticket.tenant_id == tenant.id, Ticket.created_at >= since)
        .group_by(Ticket.priority)
    )
    rows = result.all()

    data = []
    for row in rows:
        total = row.total
        breached = row.breached
        compliance_pct = round((total - breached) / total * 100, 1) if total > 0 else 100
        data.append({
            "priority": row.priority,
            "total": total,
            "breached": breached,
            "responded": row.responded,
            "compliance_pct": compliance_pct,
        })

    return {"period_days": days, "data": data}


@router.get("/ticket-volume")
async def ticket_volume(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Ticket volume breakdown by source, type, status."""
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # By source
    by_source = await db.execute(
        select(Ticket.source, func.count(Ticket.id))
        .where(Ticket.tenant_id == tenant.id, Ticket.created_at >= since)
        .group_by(Ticket.source)
    )
    # By type
    by_type = await db.execute(
        select(Ticket.type, func.count(Ticket.id))
        .where(Ticket.tenant_id == tenant.id, Ticket.created_at >= since)
        .group_by(Ticket.type)
    )
    # By status
    by_status = await db.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(Ticket.tenant_id == tenant.id, Ticket.created_at >= since)
        .group_by(Ticket.status)
    )

    return {
        "period_days": days,
        "by_source": {r[0]: r[1] for r in by_source.all()},
        "by_type": {r[0]: r[1] for r in by_type.all()},
        "by_status": {r[0]: r[1] for r in by_status.all()},
    }


@router.get("/escalation-frequency")
async def escalation_frequency(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Escalation event frequency by level."""
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(TicketEvent.new_value, func.count(TicketEvent.id))
        .where(
            TicketEvent.tenant_id == tenant.id,
            TicketEvent.event_type == "escalation",
            TicketEvent.created_at >= since,
        )
        .group_by(TicketEvent.new_value)
    )

    return {
        "period_days": days,
        "by_level": {f"L{r[0]}": r[1] for r in result.all()},
    }


@router.get("/agent-performance")
async def agent_performance(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Agent workload and resolution metrics."""
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            Ticket.assigned_user_id,
            func.count(Ticket.id).label("assigned"),
            func.count(case((Ticket.status == "resolved", 1))).label("resolved"),
            func.count(case((Ticket.status == "closed", 1))).label("closed"),
            func.count(case((Ticket.sla_breached == True, 1))).label("breached"),
        )
        .where(
            Ticket.tenant_id == tenant.id,
            Ticket.created_at >= since,
            Ticket.assigned_user_id != None,
        )
        .group_by(Ticket.assigned_user_id)
    )

    data = []
    for row in result.all():
        data.append({
            "user_id": str(row.assigned_user_id),
            "assigned": row.assigned,
            "resolved": row.resolved,
            "closed": row.closed,
            "breached": row.breached,
        })

    return {"period_days": days, "agents": data}


@router.get("/call-analytics")
async def call_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Voice call metrics: volume, duration, cost, providers."""
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(CallRecord.id).label("total_calls"),
            func.sum(CallRecord.duration_seconds).label("total_duration"),
            func.avg(CallRecord.duration_seconds).label("avg_duration"),
            func.sum(CallRecord.cost_stt + CallRecord.cost_llm + CallRecord.cost_tts).label("total_cost"),
        )
        .where(CallRecord.tenant_id == tenant.id, CallRecord.created_at >= since)
    )
    row = result.one()

    return {
        "period_days": days,
        "total_calls": row.total_calls or 0,
        "total_duration_seconds": int(row.total_duration or 0),
        "avg_duration_seconds": round(float(row.avg_duration or 0), 1),
        "total_cost": round(float(row.total_cost or 0), 4),
    }
