"""Jira integration API endpoints."""

from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.core.security import encrypt_value
from app.models.jira_config import JiraConfig
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


class JiraConfigUpdate(BaseModel):
    site_url: str
    api_email: str
    api_token: str
    status_mapping: dict | None = None
    priority_mapping: dict | None = None
    field_mapping: dict | None = None
    sync_enabled: bool = True


class JiraConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    site_url: str
    api_email: str
    sync_enabled: bool
    status_mapping: dict | None
    priority_mapping: dict | None
    last_sync_at: str | None

    model_config = {"from_attributes": True}


@router.get("/config", response_model=JiraConfigResponse | None)
async def get_jira_config(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JiraConfig).where(JiraConfig.tenant_id == tenant.id)
    )
    return result.scalar_one_or_none()


@router.put("/config", response_model=JiraConfigResponse)
async def update_jira_config(
    body: JiraConfigUpdate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JiraConfig).where(JiraConfig.tenant_id == tenant.id)
    )
    config = result.scalar_one_or_none()

    encrypted_token = encrypt_value(body.api_token)

    if config:
        config.site_url = body.site_url
        config.api_email = body.api_email
        config.api_token_encrypted = encrypted_token
        config.status_mapping = body.status_mapping
        config.priority_mapping = body.priority_mapping
        config.field_mapping = body.field_mapping
        config.sync_enabled = body.sync_enabled
    else:
        config = JiraConfig(
            tenant_id=tenant.id,
            site_url=body.site_url,
            api_email=body.api_email,
            api_token_encrypted=encrypted_token,
            status_mapping=body.status_mapping,
            priority_mapping=body.priority_mapping,
            field_mapping=body.field_mapping,
            sync_enabled=body.sync_enabled,
        )
        db.add(config)

    await db.flush()
    return config


@router.post("/test-connection")
async def test_connection(
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.jira.service import get_jira_client

    result = await get_jira_client(db, tenant.id)
    if not result:
        return {"status": "error", "message": "Jira not configured"}

    client, _ = result
    try:
        user_info = await client.test_connection()
        return {"status": "ok", "user": user_info.get("displayName")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/webhooks")
async def jira_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive Jira webhooks for inbound sync."""
    payload = await request.json()

    from app.modules.jira.service import process_jira_webhook
    result = await process_jira_webhook(db, payload)
    return result


@router.post("/sync/{ticket_id}")
async def force_sync(
    ticket_id: UUID,
    current_user: User = Depends(require_min_role("agent_l1")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Force sync a specific ticket to Jira."""
    from app.modules.tickets.service import get_ticket
    from app.modules.jira.service import sync_ticket_to_jira

    ticket = await get_ticket(db, tenant.id, ticket_id)
    result = await sync_ticket_to_jira(db, ticket)
    return result
