"""Email processing service: webhook handling, ticket creation/update."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import publish_event
from app.models.contact import Contact
from app.models.email_message import Attachment, EmailMailbox, EmailMessage
from app.models.ticket import Ticket, TicketEvent
from app.modules.contacts.service import create_contact, find_contact_by_email
from app.modules.email.parser import parse_graph_message
from app.modules.tickets.service import create_ticket as create_ticket_service


async def process_incoming_email(
    db: AsyncSession,
    mailbox_email: str,
    raw_message: dict,
) -> dict:
    """Process an incoming email and create/update a ticket.

    Args:
        db: Database session
        mailbox_email: The recipient mailbox email address
        raw_message: Full Graph API message object

    Returns:
        {"action": "created"|"updated"|"skipped", "ticket_id": str|None, ...}
    """
    parsed = parse_graph_message(raw_message)

    # Skip auto-replies
    if parsed["is_auto_reply"]:
        return {"action": "skipped", "reason": "auto_reply", "ticket_id": None}

    # Find mailbox config
    result = await db.execute(
        select(EmailMailbox).where(EmailMailbox.email_address == mailbox_email)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        return {"action": "skipped", "reason": "unknown_mailbox", "ticket_id": None}

    tenant_id = mailbox.tenant_id
    project_id = mailbox.project_id

    # Match or create contact
    contact = await find_contact_by_email(db, tenant_id, parsed["from_address"])
    if not contact:
        contact = await create_contact(
            db, tenant_id,
            name=parsed["from_name"] or parsed["from_address"].split("@")[0],
            email=parsed["from_address"],
        )

    # Check for existing ticket (thread matching)
    existing_ticket = await _find_existing_ticket(db, tenant_id, parsed)

    if existing_ticket:
        return await _update_ticket_with_email(db, existing_ticket, parsed, mailbox)
    else:
        return await _create_ticket_from_email(
            db, tenant_id, project_id, contact, parsed, mailbox,
        )


async def _find_existing_ticket(
    db: AsyncSession, tenant_id: UUID, parsed: dict,
) -> Ticket | None:
    """Try to match email to existing ticket via multiple strategies."""

    # Strategy 1: Ticket number in subject [TKT-00042]
    if parsed["ticket_number"]:
        result = await db.execute(
            select(Ticket).where(
                Ticket.tenant_id == tenant_id,
                Ticket.ticket_number == parsed["ticket_number"],
            )
        )
        ticket = result.scalar_one_or_none()
        if ticket:
            return ticket

    # Strategy 2: Match conversation_id from previous emails
    if parsed["conversation_id"]:
        result = await db.execute(
            select(EmailMessage).where(
                EmailMessage.tenant_id == tenant_id,
                EmailMessage.conversation_id == parsed["conversation_id"],
                EmailMessage.ticket_id != None,
            ).limit(1)
        )
        existing_email = result.scalar_one_or_none()
        if existing_email:
            return await db.get(Ticket, existing_email.ticket_id)

    # Strategy 3: Match in-reply-to header
    if parsed["in_reply_to"]:
        result = await db.execute(
            select(EmailMessage).where(
                EmailMessage.tenant_id == tenant_id,
                EmailMessage.graph_message_id == parsed["in_reply_to"],
                EmailMessage.ticket_id != None,
            ).limit(1)
        )
        existing_email = result.scalar_one_or_none()
        if existing_email:
            return await db.get(Ticket, existing_email.ticket_id)

    return None


async def _create_ticket_from_email(
    db: AsyncSession,
    tenant_id: UUID,
    project_id: UUID | None,
    contact: Contact,
    parsed: dict,
    mailbox: EmailMailbox,
) -> dict:
    """Create a new ticket from an incoming email."""
    # Determine priority (VIP contacts get P2 minimum)
    priority = "P2" if contact.vip else "P3"

    ticket = await create_ticket_service(
        db, tenant_id, user_id=None,
        subject=parsed["subject"] or "(No Subject)",
        description=parsed["body_text"][:5000] if parsed["body_text"] else None,
        type="incident",
        priority=priority,
        source="email",
        project_id=project_id or contact.default_project_id,
        contact_id=contact.id,
    )

    # Store email message
    email_msg = EmailMessage(
        tenant_id=tenant_id,
        ticket_id=ticket.id,
        graph_message_id=parsed["message_id"],
        direction="inbound",
        from_address=parsed["from_address"],
        to_addresses=parsed["to_addresses"],
        cc_addresses=parsed["cc_addresses"],
        subject=parsed["subject"],
        body_text=parsed["body_text"],
        body_html=parsed["body_html"],
        has_attachments=parsed["has_attachments"],
        conversation_id=parsed["conversation_id"],
        in_reply_to=parsed["in_reply_to"],
        received_at=parsed["received_at"],
        sent_at=parsed["sent_at"],
    )
    db.add(email_msg)

    # Store source references on ticket
    ticket.source_email_id = parsed["message_id"]
    ticket.source_conversation_id = parsed["conversation_id"]

    await db.flush()

    return {
        "action": "created",
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
        "contact_id": str(contact.id),
    }


async def _update_ticket_with_email(
    db: AsyncSession,
    ticket: Ticket,
    parsed: dict,
    mailbox: EmailMailbox,
) -> dict:
    """Add incoming email as a reply to existing ticket."""
    email_msg = EmailMessage(
        tenant_id=ticket.tenant_id,
        ticket_id=ticket.id,
        graph_message_id=parsed["message_id"],
        direction="inbound",
        from_address=parsed["from_address"],
        to_addresses=parsed["to_addresses"],
        cc_addresses=parsed["cc_addresses"],
        subject=parsed["subject"],
        body_text=parsed["body_text"],
        body_html=parsed["body_html"],
        has_attachments=parsed["has_attachments"],
        conversation_id=parsed["conversation_id"],
        in_reply_to=parsed["in_reply_to"],
        received_at=parsed["received_at"],
        sent_at=parsed["sent_at"],
    )
    db.add(email_msg)

    # Create timeline event
    event = TicketEvent(
        tenant_id=ticket.tenant_id,
        ticket_id=ticket.id,
        event_type="email_received",
        comment=f"Email from {parsed['from_address']}: {parsed['subject']}",
        is_public=True,
        metadata_={"from": parsed["from_address"], "message_id": parsed["message_id"]},
    )
    db.add(event)

    # Resume SLA if was pending_customer
    if ticket.status == "pending_customer":
        ticket.status = "in_progress"
        ticket.sla_paused_at = None
        resume_event = TicketEvent(
            tenant_id=ticket.tenant_id,
            ticket_id=ticket.id,
            event_type="status_change",
            old_value="pending_customer",
            new_value="in_progress",
            metadata_={"trigger": "customer_email_reply"},
        )
        db.add(resume_event)

    await db.flush()

    await publish_event(
        str(ticket.tenant_id),
        "ticket.updated",
        {"ticket_id": str(ticket.id), "event": "email_received"},
    )

    return {
        "action": "updated",
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
    }
