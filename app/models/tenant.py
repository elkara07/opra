"""Tenant model."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import IDMixin, TimestampMixin


class Tenant(Base, IDMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    plan: Mapped[str] = mapped_column(String(20), default="starter")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # JSONB config fields
    business_hours: Mapped[dict | None] = mapped_column(JSONB, default=None)
    holidays: Mapped[list | None] = mapped_column(JSONB, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")
    projects = relationship("Project", back_populates="tenant", lazy="selectin")
