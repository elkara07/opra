"""Projects API: CRUD, stats, Jira mapping, CSV import."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


# --- Schemas ---

class ProjectCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    jira_project_key: str | None = None
    default_team_id: UUID | None = None
    default_priority: str = "P3"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    jira_project_key: str | None = None
    default_team_id: UUID | None = None
    default_priority: str | None = None
    is_active: bool | None = None


class ProjectResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: str | None = None
    jira_project_key: str | None = None
    jira_project_id: str | None = None
    default_team_id: UUID | None = None
    default_priority: str
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectStatsResponse(BaseModel):
    id: UUID
    name: str
    code: str
    jira_project_key: str | None
    is_active: bool
    total_tickets: int
    open_tickets: int
    breached_tickets: int
    by_priority: dict
    by_status: dict
    escalated_count: int


# --- Endpoints ---

@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.tenant_id == tenant.id).order_by(Project.code)
    )
    return list(result.scalars().all())


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    # Check code uniqueness within tenant
    existing = await db.execute(
        select(Project).where(Project.tenant_id == tenant.id, Project.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Project code '{body.code}' already exists")

    project = Project(tenant_id=tenant.id, **body.model_dump())
    db.add(project)
    await db.flush()
    return project


@router.get("/stats", response_model=list[ProjectStatsResponse])
async def list_projects_with_stats(
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all projects with ticket statistics — for dashboard project cards."""
    projects_result = await db.execute(
        select(Project).where(Project.tenant_id == tenant.id).order_by(Project.code)
    )
    projects = list(projects_result.scalars().all())

    result = []
    for proj in projects:
        # Ticket stats for this project
        tickets_result = await db.execute(
            select(Ticket).where(
                Ticket.tenant_id == tenant.id,
                Ticket.project_id == proj.id,
            )
        )
        tickets = list(tickets_result.scalars().all())

        open_statuses = {"new", "assigned", "in_progress", "pending_customer", "pending_vendor"}
        open_tickets = [t for t in tickets if t.status in open_statuses]
        breached = [t for t in tickets if t.sla_breached]
        escalated = [t for t in open_tickets if t.current_escalation_level > 0]

        by_priority = {}
        by_status = {}
        for t in open_tickets:
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
            by_status[t.status] = by_status.get(t.status, 0) + 1

        result.append(ProjectStatsResponse(
            id=proj.id,
            name=proj.name,
            code=proj.code,
            jira_project_key=proj.jira_project_key,
            is_active=proj.is_active,
            total_tickets=len(tickets),
            open_tickets=len(open_tickets),
            breached_tickets=len(breached),
            by_priority=by_priority,
            by_status=by_status,
            escalated_count=len(escalated),
        ))

    return result


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(require_min_role("viewer")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant.id)
    )
    proj = result.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project")
    return proj


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant.id)
    )
    proj = result.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(proj, field, value)
    await db.flush()
    return proj


@router.put("/{project_id}/jira-mapping")
async def update_jira_mapping(
    project_id: UUID,
    jira_project_key: str = Query(...),
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Map a project to a Jira project key."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant.id)
    )
    proj = result.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project")

    proj.jira_project_key = jira_project_key
    await db.flush()
    return {"project_id": str(proj.id), "code": proj.code, "jira_project_key": jira_project_key}


@router.post("/import-csv")
async def import_projects_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Import projects from CSV. Columns: code, name, description, jira_project_key, default_priority.

    Existing projects (matched by code) are updated. New ones are created.
    """
    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    updated = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        if not code or not name:
            errors.append(f"Row {row_num}: missing code or name")
            continue

        result = await db.execute(
            select(Project).where(Project.tenant_id == tenant.id, Project.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = name
            if row.get("description"):
                existing.description = row["description"].strip()
            if row.get("jira_project_key"):
                existing.jira_project_key = row["jira_project_key"].strip()
            if row.get("default_priority"):
                existing.default_priority = row["default_priority"].strip()
            updated += 1
        else:
            proj = Project(
                tenant_id=tenant.id,
                code=code,
                name=name,
                description=(row.get("description") or "").strip() or None,
                jira_project_key=(row.get("jira_project_key") or "").strip() or None,
                default_priority=(row.get("default_priority") or "P3").strip(),
            )
            db.add(proj)
            created += 1

    await db.flush()
    return {"created": created, "updated": updated, "errors": errors}
