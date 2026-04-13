"""Escalation rule model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin


class EscalationRule(Base, IDMixin, TenantMixin):
    __tablename__ = "escalation_rules"

    sla_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sla_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notify_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"),
    )
    notify_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )
    notification_channels: Mapped[list | None] = mapped_column(
        JSONB, default=lambda: ["email"],
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
