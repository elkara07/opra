"""FastAPI dependencies: auth, tenant isolation, RBAC."""

from __future__ import annotations

import hmac
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.tenant import Tenant
from app.models.user import User


# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return User."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    token = authorization[7:]
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    user = await db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Resolve tenant from authenticated user."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no tenant association",
        )
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not found or inactive",
        )
    return tenant


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

ROLE_HIERARCHY = {
    "super_admin": 100,
    "tenant_admin": 90,
    "manager": 70,
    "agent_l3": 50,
    "agent_l2": 40,
    "agent_l1": 30,
    "viewer": 10,
}


def require_role(*allowed_roles: str):
    """Return a dependency that checks the user has one of the allowed roles."""

    def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not permitted. Required: {allowed_roles}",
            )
        return current_user

    return _check


def require_min_role(min_role: str):
    """Return a dependency that checks user's role level >= min_role level."""
    min_level = ROLE_HIERARCHY.get(min_role, 0)

    def _check(current_user: User = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role level. Required: {min_role} or higher",
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# Service-to-service auth
# ---------------------------------------------------------------------------

async def verify_service_key(
    x_service_key: Annotated[str, Header()],
):
    """Timing-safe comparison of internal service key."""
    expected = settings.internal_service_key.encode()
    provided = x_service_key.encode()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service key",
        )
