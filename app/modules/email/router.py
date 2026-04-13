"""Email API endpoints: webhook receiver, mailbox management."""

from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_min_role
from app.models.email_message import EmailMailbox
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Microsoft Graph webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/webhooks/graph")
async def graph_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Microsoft Graph change notifications.

    Two scenarios:
    1. Subscription validation: Graph sends a validationToken query param
    2. Notification: Graph sends JSON with changed resources
    """
    # Subscription validation handshake
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return Response(content=validation_token, media_type="text/plain")

    # Process notification
    body = await request.json()
    notifications = body.get("value", [])

    from workers.tasks.email_tasks import process_email_notification

    for notification in notifications:
        # Verify client state
        client_state = notification.get("clientState", "")
        if not hmac.compare_digest(
            client_state.encode(), settings.ms_graph_webhook_secret.encode()
        ):
            continue

        # Extract resource info
        resource = notification.get("resource", "")
        # resource format: /users/{mailbox_id}/messages/{message_id}
        parts = resource.strip("/").split("/")
        if len(parts) >= 4 and parts[2] == "messages":
            mailbox_id = parts[1]
            message_id = parts[3]

            # Queue for async processing
            process_email_notification.delay({
                "mailbox_id": mailbox_id,
                "message_id": message_id,
                "change_type": notification.get("changeType"),
                "tenant_id": notification.get("tenantId"),
            })

    return {"status": "accepted"}


# ---------------------------------------------------------------------------
# Mailbox management
# ---------------------------------------------------------------------------

class MailboxCreate(BaseModel):
    email_address: str
    display_name: str | None = None
    ms_user_id: str
    project_id: UUID | None = None


class MailboxResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email_address: str
    display_name: str | None
    ms_user_id: str | None
    graph_subscription_id: str | None
    project_id: UUID | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("/mailboxes", response_model=list[MailboxResponse])
async def list_mailboxes(
    current_user: User = Depends(require_min_role("manager")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMailbox).where(EmailMailbox.tenant_id == tenant.id)
    )
    return list(result.scalars().all())


@router.post("/mailboxes", response_model=MailboxResponse, status_code=201)
async def create_mailbox(
    body: MailboxCreate,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    mailbox = EmailMailbox(
        tenant_id=tenant.id,
        email_address=body.email_address,
        display_name=body.display_name,
        ms_user_id=body.ms_user_id,
        project_id=body.project_id,
    )
    db.add(mailbox)
    await db.flush()
    return mailbox


@router.delete("/mailboxes/{mailbox_id}")
async def delete_mailbox(
    mailbox_id: UUID,
    current_user: User = Depends(require_min_role("tenant_admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMailbox).where(
            EmailMailbox.id == mailbox_id,
            EmailMailbox.tenant_id == tenant.id,
        )
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Mailbox")

    # Delete Graph subscription if exists
    if mailbox.graph_subscription_id:
        try:
            from app.modules.email.graph_client import delete_subscription
            import asyncio
            await delete_subscription(mailbox.graph_subscription_id)
        except Exception:
            pass  # Best effort

    await db.delete(mailbox)
    await db.flush()
    return {"detail": "Mailbox deleted"}
