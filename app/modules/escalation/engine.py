"""Escalation engine: threshold evaluation and level management."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import publish_event
from app.models.escalation import EscalationRule
from app.models.sla import SLAConfig
from app.models.ticket import Ticket, TicketEvent
from app.models.tenant import Tenant
from app.modules.sla.engine import calculate_business_minutes
from app.modules.sla.service import DEFAULT_SLA


async def check_escalation_for_ticket(
    db: AsyncSession, ticket: Ticket, tenant: Tenant,
) -> bool:
    """Check if a ticket needs escalation based on elapsed time vs thresholds.

    Returns True if escalation was triggered.
    """
    if ticket.status in ("resolved", "closed", "cancelled"):
        return False
    if ticket.sla_paused_at:
        return False

    now = datetime.now(timezone.utc)
    bh = tenant.business_hours or {}
    holidays = tenant.holidays or []
    tz = tenant.timezone or "UTC"

    elapsed = calculate_business_minutes(
        ticket.created_at, now, bh, holidays, tz,
    )

    # Get escalation thresholds
    thresholds = await _get_thresholds(db, ticket)

    if not thresholds:
        return False

    # Find the highest threshold that's been exceeded but not yet escalated
    for level, threshold_minutes in enumerate(thresholds, start=1):
        if elapsed >= threshold_minutes and ticket.current_escalation_level < level:
            await _escalate_ticket(db, ticket, tenant, level, elapsed)
            return True

    return False


async def _get_thresholds(db: AsyncSession, ticket: Ticket) -> list[int]:
    """Get escalation thresholds for a ticket.

    Priority: DB escalation_rules > SLA config thresholds > defaults.
    """
    # Try DB escalation rules
    result = await db.execute(
        select(EscalationRule)
        .where(
            EscalationRule.tenant_id == ticket.tenant_id,
            EscalationRule.is_active == True,
        )
        .order_by(EscalationRule.level)
    )
    rules = list(result.scalars().all())

    if rules:
        # If rules reference a specific SLA config, filter to matching ones
        if ticket.sla_config_id:
            matching = [r for r in rules if r.sla_config_id == ticket.sla_config_id]
            if matching:
                return [r.threshold_minutes for r in matching]

        # Generic rules (no sla_config_id filter)
        return [r.threshold_minutes for r in rules]

    # Try SLA config escalation_thresholds JSON
    if ticket.sla_config_id:
        sla = await db.get(SLAConfig, ticket.sla_config_id)
        if sla and sla.escalation_thresholds:
            return sla.escalation_thresholds

    # Use defaults
    defaults = DEFAULT_SLA.get(ticket.priority, DEFAULT_SLA["P3"])
    return defaults.get("escalation", [])


async def _escalate_ticket(
    db: AsyncSession,
    ticket: Ticket,
    tenant: Tenant,
    new_level: int,
    elapsed_minutes: int,
):
    """Perform the escalation: bump level, create event, notify."""
    old_level = ticket.current_escalation_level
    ticket.current_escalation_level = new_level

    # Find the escalation rule for team reassignment
    result = await db.execute(
        select(EscalationRule).where(
            EscalationRule.tenant_id == ticket.tenant_id,
            EscalationRule.level == new_level,
            EscalationRule.is_active == True,
        )
    )
    rule = result.scalar_one_or_none()

    # Reassign to escalation team/user if configured
    if rule:
        if rule.notify_team_id:
            ticket.assigned_team_id = rule.notify_team_id
        if rule.notify_user_id:
            ticket.assigned_user_id = rule.notify_user_id

    # Create escalation event
    event = TicketEvent(
        tenant_id=ticket.tenant_id,
        ticket_id=ticket.id,
        event_type="escalation",
        old_value=str(old_level),
        new_value=str(new_level),
        metadata_={
            "elapsed_minutes": elapsed_minutes,
            "rule_id": str(rule.id) if rule else None,
            "channels": rule.notification_channels if rule else ["email"],
        },
    )
    db.add(event)
    await db.flush()

    # Publish real-time event
    await publish_event(
        str(ticket.tenant_id),
        "ticket.escalated",
        {
            "ticket_id": str(ticket.id),
            "ticket_number": ticket.ticket_number,
            "priority": ticket.priority,
            "old_level": old_level,
            "new_level": new_level,
            "elapsed_minutes": elapsed_minutes,
        },
    )


async def manual_escalate(
    db: AsyncSession,
    ticket: Ticket,
    user_id: UUID,
    target_level: int | None = None,
) -> Ticket:
    """Manually escalate a ticket to next or specified level."""
    new_level = target_level or (ticket.current_escalation_level + 1)
    if new_level > 4:
        new_level = 4

    old_level = ticket.current_escalation_level
    ticket.current_escalation_level = new_level

    event = TicketEvent(
        tenant_id=ticket.tenant_id,
        ticket_id=ticket.id,
        event_type="escalation",
        old_value=str(old_level),
        new_value=str(new_level),
        user_id=user_id,
        metadata_={"manual": True},
    )
    db.add(event)
    await db.flush()

    await publish_event(
        str(ticket.tenant_id),
        "ticket.escalated",
        {
            "ticket_id": str(ticket.id),
            "ticket_number": ticket.ticket_number,
            "new_level": new_level,
            "manual": True,
        },
    )

    return ticket
