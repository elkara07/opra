"""Auth business logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.user import RefreshToken, User


async def authenticate_user(
    db: AsyncSession, email: str, password: str, tenant_slug: str | None = None,
) -> User:
    """Verify credentials and return user."""
    query = select(User).where(User.email == email, User.is_active == True)
    if tenant_slug:
        query = query.join(Tenant).where(Tenant.slug == tenant_slug)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise NotFoundError("User", "Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise NotFoundError("User", "Invalid credentials")
    return user


def issue_tokens(user: User) -> dict:
    """Create access + refresh token pair."""
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }


async def store_refresh_token(
    db: AsyncSession, user_id: UUID, token: str,
) -> RefreshToken:
    """Persist refresh token for revocation tracking."""
    rt = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(rt)
    await db.flush()
    return rt


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    """Validate refresh token and issue new pair."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise NotFoundError("Token", "Invalid refresh token")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked_at == None,
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise NotFoundError("Token", "Refresh token not found or revoked")

    # Revoke old token
    stored.revoked_at = datetime.now(timezone.utc)

    user = await db.get(User, stored.user_id)
    if not user or not user.is_active:
        raise NotFoundError("User", "User not found or inactive")

    tokens = issue_tokens(user)
    await store_refresh_token(db, user.id, tokens["refresh_token"])
    return tokens


async def revoke_refresh_token(db: AsyncSession, token: str):
    """Revoke a refresh token (logout)."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked_at = datetime.now(timezone.utc)


async def register_tenant(
    db: AsyncSession,
    tenant_name: str,
    tenant_slug: str,
    email: str,
    name: str,
    password: str,
) -> dict:
    """Create a new tenant with an admin user."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Tenant slug '{tenant_slug}' already exists")

    tenant = Tenant(
        name=tenant_name,
        slug=tenant_slug,
        business_hours={
            "mon": {"start": "09:00", "end": "18:00"},
            "tue": {"start": "09:00", "end": "18:00"},
            "wed": {"start": "09:00", "end": "18:00"},
            "thu": {"start": "09:00", "end": "18:00"},
            "fri": {"start": "09:00", "end": "18:00"},
        },
    )
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        name=name,
        password_hash=hash_password(password),
        role="tenant_admin",
    )
    db.add(user)
    await db.flush()

    tokens = issue_tokens(user)
    await store_refresh_token(db, user.id, tokens["refresh_token"])

    return {
        "tenant_id": tenant.id,
        "user_id": user.id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }
