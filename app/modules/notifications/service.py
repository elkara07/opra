"""Notification dispatch service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationLog


async def log_notification(
    db: AsyncSession,
    tenant_id: UUID,
    ticket_id: UUID | None,
    channel: str,
    recipient: str,
    subject: str,
    template: str | None = None,
    status: str = "queued",
) -> NotificationLog:
    """Create a notification log entry."""
    log = NotificationLog(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        channel=channel,
        recipient=recipient,
        subject=subject,
        template=template,
        status=status,
    )
    db.add(log)
    await db.flush()
    return log
