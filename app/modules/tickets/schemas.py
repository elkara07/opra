"""Ticket Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ticket import TICKET_PRIORITIES, TICKET_SOURCES, TICKET_STATUSES, TICKET_TYPES


class TicketCreate(BaseModel):
    subject: str = Field(max_length=500)
    description: str | None = None
    type: str = Field(default="incident")
    priority: str = Field(default="P3")
    source: str = Field(default="web")
    project_id: UUID | None = None
    contact_id: UUID | None = None
    assigned_team_id: UUID | None = None
    assigned_user_id: UUID | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, max_length=500)
    description: str | None = None
    priority: str | None = None
    assigned_team_id: UUID | None = None
    assigned_user_id: UUID | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None


class TicketStatusChange(BaseModel):
    status: str


class TicketAssign(BaseModel):
    team_id: UUID | None = None
    user_id: UUID | None = None


class CommentCreate(BaseModel):
    comment: str
    is_public: bool = False


class TicketResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    ticket_number: str
    type: str
    status: str
    priority: str
    subject: str
    description: str | None
    source: str
    project_id: UUID | None
    contact_id: UUID | None
    assigned_team_id: UUID | None
    assigned_user_id: UUID | None
    current_escalation_level: int
    sla_response_due: datetime | None
    sla_resolution_due: datetime | None
    sla_responded_at: datetime | None
    sla_breached: bool
    jira_issue_key: str | None
    jira_sync_status: str | None
    tags: list | None
    custom_fields: dict | None
    created_at: datetime
    updated_at: datetime | None
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class TicketEventResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    event_type: str
    old_value: str | None
    new_value: str | None
    comment: str | None
    is_public: bool
    user_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    size: int
