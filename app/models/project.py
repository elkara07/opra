"""Project model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


class Project(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    jira_project_key: Mapped[str | None] = mapped_column(String(20))
    jira_project_id: Mapped[str | None] = mapped_column(String(50))
    default_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
    )
    default_priority: Mapped[str] = mapped_column(String(5), default="P3")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    tenant = relationship("Tenant", back_populates="projects")
