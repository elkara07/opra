"""SLA and escalation periodic tasks.

These run every 60 seconds via Celery Beat and check all active tickets
across all tenants for SLA breaches and escalation thresholds.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from workers.celery_app import app


def _run_async(coro):
    """Run an async function from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _sla_check_all_async():
    """Check SLA timers for all active tickets."""
    from app.core.database import async_session_factory
    from app.models.ticket import Ticket, TicketEvent
    from app.models.tenant import Tenant
    from app.modules.sla.engine import calculate_business_minutes, evaluate_sla_status
    from app.core.events import publish_event

    async with async_session_factory() as db:
        # Get all active tickets with SLA configured
        result = await db.execute(
            select(Ticket).where(
                Ticket.status.notin_(["resolved", "closed", "cancelled"]),
                Ticket.sla_response_due != None,
                Ticket.sla_paused_at == None,
            )
        )
        tickets = list(result.scalars().all())

        breached_count = 0
        warning_count = 0
        now = datetime.now(timezone.utc)

        for ticket in tickets:
            sla_status = evaluate_sla_status(
                created_at=ticket.created_at,
                sla_response_due=ticket.sla_response_due,
                sla_resolution_due=ticket.sla_resolution_due,
                sla_responded_at=ticket.sla_responded_at,
                sla_resolved_at=ticket.sla_resolved_at,
                sla_paused_at=ticket.sla_paused_at,
                now=now,
            )

            for sla_type in ("response", "resolution"):
                status = sla_status[sla_type]["status"]

                if status == "breached" and not ticket.sla_breached:
                    ticket.sla_breached = True
                    event = TicketEvent(
                        tenant_id=ticket.tenant_id,
                        ticket_id=ticket.id,
                        event_type="sla_breach",
                        new_value=sla_type,
                        metadata_={
                            "sla_type": sla_type,
                            "pct": sla_status[sla_type]["pct"],
                        },
                    )
                    db.add(event)
                    breached_count += 1

                    await publish_event(
                        str(ticket.tenant_id),
                        "sla.breach",
                        {
                            "ticket_id": str(ticket.id),
                            "ticket_number": ticket.ticket_number,
                            "sla_type": sla_type,
                            "priority": ticket.priority,
                        },
                    )

                elif status == "warning":
                    warning_count += 1
                    await publish_event(
                        str(ticket.tenant_id),
                        "sla.warning",
                        {
                            "ticket_id": str(ticket.id),
                            "ticket_number": ticket.ticket_number,
                            "sla_type": sla_type,
                            "remaining_minutes": sla_status[sla_type]["remaining_minutes"],
                            "pct": sla_status[sla_type]["pct"],
                        },
                    )

        await db.commit()
        return {"checked": len(tickets), "breached": breached_count, "warnings": warning_count}


async def _escalation_check_async():
    """Check escalation thresholds for all active tickets."""
    from app.core.database import async_session_factory
    from app.models.ticket import Ticket
    from app.models.tenant import Tenant
    from app.modules.escalation.engine import check_escalation_for_ticket

    async with async_session_factory() as db:
        result = await db.execute(
            select(Ticket).where(
                Ticket.status.notin_(["resolved", "closed", "cancelled"]),
                Ticket.sla_paused_at == None,
                Ticket.current_escalation_level < 4,
            )
        )
        tickets = list(result.scalars().all())

        escalated_count = 0
        # Cache tenants to avoid repeated queries
        tenant_cache: dict = {}

        for ticket in tickets:
            tid = ticket.tenant_id
            if tid not in tenant_cache:
                tenant_cache[tid] = await db.get(Tenant, tid)

            tenant = tenant_cache[tid]
            if not tenant:
                continue

            was_escalated = await check_escalation_for_ticket(db, ticket, tenant)
            if was_escalated:
                escalated_count += 1

        await db.commit()
        return {"checked": len(tickets), "escalated": escalated_count}


@app.task(name="workers.tasks.sla_tasks.sla_check_all", bind=True, max_retries=3)
def sla_check_all(self):
    """Check SLA timers for all active tickets across all tenants."""
    try:
        return _run_async(_sla_check_all_async())
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@app.task(name="workers.tasks.sla_tasks.escalation_check", bind=True, max_retries=3)
def escalation_check(self):
    """Check escalation thresholds for all active tickets."""
    try:
        return _run_async(_escalation_check_async())
    except Exception as exc:
        self.retry(exc=exc, countdown=30)
