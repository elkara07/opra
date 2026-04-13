"""Ticket and TicketEvent models — core of the system."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


# Valid ITIL v4 ticket types
TICKET_TYPES = ("incident", "service_request", "problem", "change")

# Ticket status state machine
TICKET_STATUSES = (
    "new", "assigned", "in_progress",
    "pending_customer", "pending_vendor",
    "resolved", "closed", "cancelled",
)

# Valid transitions: {current_status: [allowed_next_statuses]}
TICKET_TRANSITIONS = {
    "new": ["assigned", "in_progress", "cancelled"],
    "assigned": ["in_progress", "pending_customer", "pending_vendor", "cancelled"],
    "in_progress": ["pending_customer", "pending_vendor", "resolved", "cancelled"],
    "pending_customer": ["in_progress", "resolved", "cancelled"],
    "pending_vendor": ["in_progress", "resolved", "cancelled"],
    "resolved": ["closed", "in_progress"],  # Reopen allowed
    "closed": [],  # Terminal state
    "cancelled": [],  # Terminal state
}

TICKET_PRIORITIES = ("P1", "P2", "P3", "P4")
TICKET_SOURCES = ("email", "phone", "web", "api")


class Ticket(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_ticket_tenant_status", "tenant_id", "status"),
        Index("ix_ticket_tenant_priority_status", "tenant_id", "priority", "status"),
        Index("ix_ticket_tenant_assigned", "tenant_id", "assigned_user_id", "status"),
        Index("ix_ticket_jira_key", "jira_issue_key"),
        Index("ix_ticket_conversation", "source_conversation_id"),
    )

    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="incident")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new")
    priority: Mapped[str] = mapped_column(String(5), nullable=False, default="P3")
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")

    # Relationships
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"),
    )
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"),
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )

    # SLA tracking
    sla_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sla_configs.id", ondelete="SET NULL"),
    )
    sla_response_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_resolution_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    sla_paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_elapsed_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Escalation
    current_escalation_level: Mapped[int] = mapped_column(Integer, default=0)

    # Jira sync
    jira_issue_key: Mapped[str | None] = mapped_column(String(30))
    jira_issue_id: Mapped[str | None] = mapped_column(String(50))
    jira_sync_status: Mapped[str | None] = mapped_column(String(20))
    jira_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Source metadata
    source_email_id: Mapped[str | None] = mapped_column(String(200))
    source_call_sid: Mapped[str | None] = mapped_column(String(200))
    source_conversation_id: Mapped[str | None] = mapped_column(String(200))

    # Flexible fields
    tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ORM relationships
    events = relationship("TicketEvent", back_populates="ticket", lazy="selectin",
                          order_by="TicketEvent.created_at")


class TicketEvent(Base, IDMixin, TenantMixin):
    __tablename__ = "ticket_events"
    __table_args__ = (
        Index("ix_ticket_event_ticket_time", "ticket_id", "created_at"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(200))
    new_value: Mapped[str | None] = mapped_column(String(200))
    comment: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=__import__("datetime").timezone.utc),
    )

    ticket = relationship("Ticket", back_populates="events")
