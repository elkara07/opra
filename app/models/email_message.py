"""Email message and mailbox models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


class EmailMailbox(Base, IDMixin, TenantMixin):
    __tablename__ = "email_mailboxes"

    email_address: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    ms_user_id: Mapped[str | None] = mapped_column(String(200))
    graph_subscription_id: Mapped[str | None] = mapped_column(String(200))
    subscription_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class EmailMessage(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "email_messages"

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"),
    )
    graph_message_id: Mapped[str | None] = mapped_column(String(200))
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    from_address: Mapped[str] = mapped_column(String(200), nullable=False)
    to_addresses: Mapped[list | None] = mapped_column(JSONB)
    cc_addresses: Mapped[list | None] = mapped_column(JSONB)
    subject: Mapped[str | None] = mapped_column(String(500))
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    conversation_id: Mapped[str | None] = mapped_column(String(200))
    in_reply_to: Mapped[str | None] = mapped_column(String(200))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attachment(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "attachments"

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"),
    )
    email_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_messages.id", ondelete="SET NULL"),
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column()
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64))
