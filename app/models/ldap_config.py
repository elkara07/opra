"""LDAP configuration model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin


class LDAPConfig(Base, IDMixin, TenantMixin):
    __tablename__ = "ldap_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_ldap_config_tenant"),
    )

    server_url: Mapped[str] = mapped_column(String(500), nullable=False)
    bind_dn: Mapped[str] = mapped_column(String(500), nullable=False)
    bind_password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    base_dn: Mapped[str] = mapped_column(String(500), nullable=False)
    user_search_filter: Mapped[str] = mapped_column(String(500))
    group_search_filter: Mapped[str | None] = mapped_column(String(500))
    role_mapping: Mapped[dict | None] = mapped_column(JSONB)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
