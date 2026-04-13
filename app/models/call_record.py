"""Call record model for voice pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import IDMixin, TenantMixin, TimestampMixin


class CallRecord(Base, IDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "call_records"

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"),
    )
    call_sid: Mapped[str] = mapped_column(String(200), nullable=False)
    caller_number: Mapped[str | None] = mapped_column(String(30))
    did_number: Mapped[str | None] = mapped_column(String(30))
    direction: Mapped[str] = mapped_column(String(10), default="inbound")
    status: Mapped[str] = mapped_column(String(20), default="ringing")
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    recording_url: Mapped[str | None] = mapped_column(String(500))
    recording_storage_path: Mapped[str | None] = mapped_column(String(500))
    transcript: Mapped[str | None] = mapped_column(Text)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB)
    llm_provider: Mapped[str | None] = mapped_column(String(30))
    stt_provider: Mapped[str | None] = mapped_column(String(30))
    tts_provider: Mapped[str | None] = mapped_column(String(30))
    cost_stt: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    cost_llm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    cost_tts: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
