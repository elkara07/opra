"""LDAP configuration and sync API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.core.security import encrypt_value
from app.models.ldap_config import LDAPConfig
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


class LDAPConfigUpdate(BaseModel):
    server_url: str
    bind_dn: str
    bind_password: str
    base_dn: str
    user_search_filter: str | None = None
    group_search_filter: str | None = None
    role_mapping: dict | None = None
    sync_enabled: bool = True
    sync_interval_minutes: int = 60


class LDAPConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    server_url: str
    bind_dn: str
    base_dn: str
    user_search_filter: str | None
    role_mapping: dict | None
    sync_enabled: bool
    sync_interval_minutes: int
    last_sync_at: str | None

    model_config = {"from_attributes": True}


@router.get("/config", response_model=LDAPConfigResponse | None)
async def get_ldap_config(
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LDAPConfig).where(LDAPConfig.tenant_id == tenant.id)
    )
    return result.scalar_one_or_none()


@router.put("/config", response_model=LDAPConfigResponse)
async def update_ldap_config(
    body: LDAPConfigUpdate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LDAPConfig).where(LDAPConfig.tenant_id == tenant.id)
    )
    config = result.scalar_one_or_none()

    encrypted_pw = encrypt_value(body.bind_password)

    if config:
        config.server_url = body.server_url
        config.bind_dn = body.bind_dn
        config.bind_password_encrypted = encrypted_pw
        config.base_dn = body.base_dn
        config.user_search_filter = body.user_search_filter
        config.group_search_filter = body.group_search_filter
        config.role_mapping = body.role_mapping
        config.sync_enabled = body.sync_enabled
        config.sync_interval_minutes = body.sync_interval_minutes
    else:
        config = LDAPConfig(
            tenant_id=tenant.id,
            server_url=body.server_url,
            bind_dn=body.bind_dn,
            bind_password_encrypted=encrypted_pw,
            base_dn=body.base_dn,
            user_search_filter=body.user_search_filter,
            group_search_filter=body.group_search_filter,
            role_mapping=body.role_mapping,
            sync_enabled=body.sync_enabled,
            sync_interval_minutes=body.sync_interval_minutes,
        )
        db.add(config)

    await db.flush()
    return config


@router.post("/test-connection")
async def test_ldap_connection(
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LDAPConfig).where(LDAPConfig.tenant_id == tenant.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return {"status": "error", "message": "LDAP not configured"}

    try:
        from app.core.security import decrypt_value
        from app.modules.ldap.client import LDAPClient

        password = decrypt_value(config.bind_password_encrypted)
        client = LDAPClient(config.server_url, config.bind_dn, password)
        client.connect()
        client.close()
        return {"status": "ok", "message": "LDAP bind successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync")
async def trigger_ldap_sync(
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Trigger manual LDAP sync for this tenant."""
    from workers.tasks.ldap_tasks import ldap_sync_all
    ldap_sync_all.delay()
    return {"status": "queued", "message": "LDAP sync task queued"}
