"""Ticket API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.modules.tickets import schemas, service

router = APIRouter()


@router.post("", response_model=schemas.TicketResponse, status_code=201)
async def create_ticket(
    body: schemas.TicketCreate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_ticket(
        db,
        tenant.id,
        current_user.id,
        subject=body.subject,
        description=body.description,
        type=body.type,
        priority=body.priority,
        source=body.source,
        project_id=body.project_id,
        contact_id=body.contact_id,
        assigned_team_id=body.assigned_team_id,
        assigned_user_id=body.assigned_user_id,
        tags=body.tags,
        custom_fields=body.custom_fields,
    )


@router.get("", response_model=schemas.TicketListResponse)
async def list_tickets(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_user_id: UUID | None = Query(None),
    project_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    tickets, total = await service.list_tickets(
        db, tenant.id,
        status=status,
        priority=priority,
        assigned_user_id=assigned_user_id,
        project_id=project_id,
        page=page,
        size=size,
    )
    return {"items": tickets, "total": total, "page": page, "size": size}


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_ticket(db, tenant.id, ticket_id)


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    body: schemas.TicketUpdate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_ticket(
        db, tenant.id, ticket_id, current_user.id,
        **body.model_dump(exclude_unset=True),
    )


@router.post("/{ticket_id}/status", response_model=schemas.TicketResponse)
async def change_status(
    ticket_id: UUID,
    body: schemas.TicketStatusChange,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.change_status(
        db, tenant.id, ticket_id, current_user.id, body.status,
    )


@router.post("/{ticket_id}/assign", response_model=schemas.TicketResponse)
async def assign_ticket(
    ticket_id: UUID,
    body: schemas.TicketAssign,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    updates = {}
    if body.team_id is not None:
        updates["assigned_team_id"] = body.team_id
    if body.user_id is not None:
        updates["assigned_user_id"] = body.user_id
    return await service.update_ticket(
        db, tenant.id, ticket_id, current_user.id, **updates,
    )


@router.post("/{ticket_id}/comments", response_model=schemas.TicketEventResponse, status_code=201)
async def add_comment(
    ticket_id: UUID,
    body: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.add_comment(
        db, tenant.id, ticket_id, current_user.id, body.comment, body.is_public,
    )


@router.get("/{ticket_id}/timeline", response_model=list[schemas.TicketEventResponse])
async def get_timeline(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_timeline(db, tenant.id, ticket_id)
