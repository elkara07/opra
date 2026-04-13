"""Jira integration config and sync log models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


class JiraConfig(Base, IDMixin, TenantMixin):
    __tablename__ = "jira_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_jira_config_tenant"),
    )

    site_url: Mapped[str] = mapped_column(String(200), nullable=False)
    api_email: Mapped[str] = mapped_column(String(200), nullable=False)
    api_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_secret: Mapped[str | None] = mapped_column(String(200))
    status_mapping: Mapped[dict | None] = mapped_column(JSONB)
    priority_mapping: Mapped[dict | None] = mapped_column(JSONB)
    field_mapping: Mapped[dict | None] = mapped_column(JSONB)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JiraSyncLog(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "jira_sync_log"

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"),
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    request_payload: Mapped[dict | None] = mapped_column(JSONB)
    response_payload: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
