"""SLA configuration and escalation rule models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


class SLAConfig(Base, IDMixin, TenantMixin):
    __tablename__ = "sla_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "priority", name="uq_sla_tenant_name_priority"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(String(5), nullable=False)
    response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    update_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_thresholds: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
    )
