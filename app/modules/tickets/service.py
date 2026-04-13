"""Ticket business logic with state machine."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import publish_event
from app.core.exceptions import InvalidStateTransition, NotFoundError, ValidationError
from app.models.ticket import (
    TICKET_PRIORITIES,
    TICKET_SOURCES,
    TICKET_TRANSITIONS,
    TICKET_TYPES,
    Ticket,
    TicketEvent,
)


async def _generate_ticket_number(db: AsyncSession, tenant_id: UUID) -> str:
    """Generate next ticket number for tenant: TKT-00001, TKT-00002, etc."""
    result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.tenant_id == tenant_id)
    )
    count = result.scalar() or 0
    return f"TKT-{count + 1:05d}"


async def create_ticket(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID | None,
    *,
    subject: str,
    description: str | None = None,
    type: str = "incident",
    priority: str = "P3",
    source: str = "web",
    project_id: UUID | None = None,
    contact_id: UUID | None = None,
    assigned_team_id: UUID | None = None,
    assigned_user_id: UUID | None = None,
    tags: list | None = None,
    custom_fields: dict | None = None,
) -> Ticket:
    """Create a new ticket with validation."""
    if type not in TICKET_TYPES:
        raise ValidationError(f"Invalid ticket type: {type}. Allowed: {TICKET_TYPES}")
    if priority not in TICKET_PRIORITIES:
        raise ValidationError(f"Invalid priority: {priority}. Allowed: {TICKET_PRIORITIES}")
    if source not in TICKET_SOURCES:
        raise ValidationError(f"Invalid source: {source}. Allowed: {TICKET_SOURCES}")

    ticket_number = await _generate_ticket_number(db, tenant_id)
    initial_status = "assigned" if (assigned_team_id or assigned_user_id) else "new"

    ticket = Ticket(
        tenant_id=tenant_id,
        ticket_number=ticket_number,
        type=type,
        status=initial_status,
        priority=priority,
        subject=subject,
        description=description,
        source=source,
        project_id=project_id,
        contact_id=contact_id,
        assigned_team_id=assigned_team_id,
        assigned_user_id=assigned_user_id,
        tags=tags or [],
        custom_fields=custom_fields or {},
    )
    db.add(ticket)
    await db.flush()

    # Create event
    event = TicketEvent(
        tenant_id=tenant_id,
        ticket_id=ticket.id,
        event_type="created",
        new_value=initial_status,
        user_id=user_id,
        metadata_={"source": source, "priority": priority},
    )
    db.add(event)
    await db.flush()

    await publish_event(
        str(tenant_id),
        "ticket.created",
        {"ticket_id": str(ticket.id), "ticket_number": ticket_number, "priority": priority},
    )

    return ticket


async def get_ticket(db: AsyncSession, tenant_id: UUID, ticket_id: UUID) -> Ticket:
    """Get a ticket by ID, scoped to tenant."""
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == tenant_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket")
    return ticket


async def list_tickets(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    status: str | None = None,
    priority: str | None = None,
    assigned_user_id: UUID | None = None,
    project_id: UUID | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[Ticket], int]:
    """List tickets with filters, tenant-scoped."""
    query = select(Ticket).where(Ticket.tenant_id == tenant_id)
    count_query = select(func.count(Ticket.id)).where(Ticket.tenant_id == tenant_id)

    if status:
        query = query.where(Ticket.status == status)
        count_query = count_query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
        count_query = count_query.where(Ticket.priority == priority)
    if assigned_user_id:
        query = query.where(Ticket.assigned_user_id == assigned_user_id)
        count_query = count_query.where(Ticket.assigned_user_id == assigned_user_id)
    if project_id:
        query = query.where(Ticket.project_id == project_id)
        count_query = count_query.where(Ticket.project_id == project_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    tickets = list(result.scalars().all())

    return tickets, total


async def update_ticket(
    db: AsyncSession,
    tenant_id: UUID,
    ticket_id: UUID,
    user_id: UUID | None,
    **updates,
) -> Ticket:
    """Update ticket fields (not status — use change_status for that)."""
    ticket = await get_ticket(db, tenant_id, ticket_id)

    for field, value in updates.items():
        if value is not None and hasattr(ticket, field):
            old_val = getattr(ticket, field)
            setattr(ticket, field, value)
            if old_val != value:
                event = TicketEvent(
                    tenant_id=tenant_id,
                    ticket_id=ticket.id,
                    event_type=f"{field}_change",
                    old_value=str(old_val) if old_val else None,
                    new_value=str(value),
                    user_id=user_id,
                )
                db.add(event)

    await db.flush()
    await publish_event(
        str(tenant_id), "ticket.updated",
        {"ticket_id": str(ticket.id), "ticket_number": ticket.ticket_number},
    )
    return ticket


async def change_status(
    db: AsyncSession,
    tenant_id: UUID,
    ticket_id: UUID,
    user_id: UUID | None,
    new_status: str,
) -> Ticket:
    """Change ticket status with state machine validation."""
    ticket = await get_ticket(db, tenant_id, ticket_id)

    allowed = TICKET_TRANSITIONS.get(ticket.status, [])
    if new_status not in allowed:
        raise InvalidStateTransition(ticket.status, new_status)

    old_status = ticket.status
    ticket.status = new_status

    # SLA clock management
    if new_status in ("pending_customer", "pending_vendor"):
        ticket.sla_paused_at = datetime.now(timezone.utc)
    elif old_status in ("pending_customer", "pending_vendor") and new_status == "in_progress":
        ticket.sla_paused_at = None

    if new_status == "resolved":
        ticket.sla_resolved_at = datetime.now(timezone.utc)
    if new_status == "closed":
        ticket.closed_at = datetime.now(timezone.utc)

    event = TicketEvent(
        tenant_id=tenant_id,
        ticket_id=ticket.id,
        event_type="status_change",
        old_value=old_status,
        new_value=new_status,
        user_id=user_id,
    )
    db.add(event)
    await db.flush()

    await publish_event(
        str(tenant_id), "ticket.updated",
        {"ticket_id": str(ticket.id), "status": new_status},
    )
    return ticket


async def add_comment(
    db: AsyncSession,
    tenant_id: UUID,
    ticket_id: UUID,
    user_id: UUID,
    comment: str,
    is_public: bool = False,
) -> TicketEvent:
    """Add a comment to a ticket."""
    ticket = await get_ticket(db, tenant_id, ticket_id)

    # First public response marks SLA response
    if is_public and not ticket.sla_responded_at:
        ticket.sla_responded_at = datetime.now(timezone.utc)

    event = TicketEvent(
        tenant_id=tenant_id,
        ticket_id=ticket.id,
        event_type="comment",
        comment=comment,
        is_public=is_public,
        is_internal=not is_public,
        user_id=user_id,
    )
    db.add(event)
    await db.flush()
    return event


async def get_timeline(
    db: AsyncSession, tenant_id: UUID, ticket_id: UUID,
) -> list[TicketEvent]:
    """Get full event timeline for a ticket."""
    # Verify ticket exists and belongs to tenant
    await get_ticket(db, tenant_id, ticket_id)
    result = await db.execute(
        select(TicketEvent)
        .where(TicketEvent.ticket_id == ticket_id, TicketEvent.tenant_id == tenant_id)
        .order_by(TicketEvent.created_at)
    )
    return list(result.scalars().all())
