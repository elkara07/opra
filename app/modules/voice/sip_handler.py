"""LiveKit SIP event handler: incoming call routing, DID→tenant mapping."""

from __future__ import annotations

from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import get_redis
from app.models.audit import DIDMapping
from app.models.tenant import Tenant


async def resolve_tenant_from_did(
    db: AsyncSession, did_number: str,
) -> dict | None:
    """Look up tenant and project from a DID number.

    Checks Redis cache first, then database.
    Returns {"tenant_id": str, "project_id": str|None, "tenant_name": str} or None.
    """
    # Redis cache lookup
    r = await get_redis()
    cache_key = f"did:{did_number}"
    cached = await r.hgetall(cache_key)
    if cached:
        return cached

    # Database lookup
    result = await db.execute(
        select(DIDMapping).where(DIDMapping.did_number == did_number)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        return None

    tenant = await db.get(Tenant, mapping.tenant_id)
    if not tenant:
        return None

    data = {
        "tenant_id": str(mapping.tenant_id),
        "project_id": str(mapping.project_id) if mapping.project_id else "",
        "tenant_name": tenant.name,
    }

    # Cache for 5 minutes
    await r.hset(cache_key, mapping=data)
    await r.expire(cache_key, 300)

    return data


async def register_did_mapping(
    db: AsyncSession,
    tenant_id: UUID,
    did_number: str,
    project_id: UUID | None = None,
    description: str | None = None,
) -> DIDMapping:
    """Register a DID number → tenant mapping."""
    mapping = DIDMapping(
        tenant_id=tenant_id,
        did_number=did_number,
        project_id=project_id,
        description=description,
    )
    db.add(mapping)
    await db.flush()

    # Invalidate cache
    r = await get_redis()
    await r.delete(f"did:{did_number}")

    return mapping
