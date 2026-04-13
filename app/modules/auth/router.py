"""Auth API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.auth import schemas, service

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse)
async def login(body: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await service.authenticate_user(db, body.email, body.password)
    tokens = service.issue_tokens(user)
    await service.store_refresh_token(db, user.id, tokens["refresh_token"])
    return tokens


@router.post("/register", response_model=schemas.RegisterResponse)
async def register(body: schemas.RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await service.register_tenant(
        db,
        tenant_name=body.tenant_name,
        tenant_slug=body.tenant_slug,
        email=body.email,
        name=body.name,
        password=body.password,
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(body: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await service.refresh_access_token(db, body.refresh_token)


@router.post("/logout")
async def logout(body: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    await service.revoke_refresh_token(db, body.refresh_token)
    return {"detail": "Logged out"}


@router.get("/me", response_model=schemas.UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
