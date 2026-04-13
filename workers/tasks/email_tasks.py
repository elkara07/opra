"""Email processing Celery tasks."""

from __future__ import annotations

import asyncio

from workers.celery_app import app


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_email_async(notification_data: dict):
    """Fetch email from Graph API, parse, create/update ticket, send auto-reply."""
    from app.core.database import async_session_factory
    from app.modules.email.graph_client import get_message, send_mail
    from app.modules.email.service import process_incoming_email
    from app.modules.notifications.templates import ticket_created_template
    from app.models.email_message import EmailMailbox
    from sqlalchemy import select

    mailbox_id = notification_data["mailbox_id"]
    message_id = notification_data["message_id"]

    async with async_session_factory() as db:
        # Find which mailbox this is
        result = await db.execute(
            select(EmailMailbox).where(EmailMailbox.ms_user_id == mailbox_id)
        )
        mailbox = result.scalar_one_or_none()
        if not mailbox:
            return {"status": "skipped", "reason": f"unknown mailbox ms_user_id={mailbox_id}"}

        # Fetch full message from Graph
        raw_message = await get_message(mailbox_id, message_id)

        # Process: match/create contact, find/create ticket
        result = await process_incoming_email(db, mailbox.email_address, raw_message)

        # Send auto-reply for newly created tickets
        if result["action"] == "created":
            subject, body_html = ticket_created_template(
                ticket_number=result["ticket_number"],
                subject=raw_message.get("subject", ""),
                priority="P3",  # Default, will be enhanced with actual priority
            )
            from_addr = raw_message.get("from", {}).get("emailAddress", {}).get("address")
            if from_addr:
                await send_mail(
                    mailbox_id=mailbox.ms_user_id,
                    to=[from_addr],
                    subject=subject,
                    body_html=body_html,
                    reply_to_message_id=message_id,
                )

        await db.commit()
        return result


async def _renew_subscriptions_async():
    """Renew all active Graph webhook subscriptions."""
    from app.core.database import async_session_factory
    from app.modules.email.graph_client import renew_subscription
    from app.models.email_message import EmailMailbox
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(
            select(EmailMailbox).where(
                EmailMailbox.is_active == True,
                EmailMailbox.graph_subscription_id != None,
            )
        )
        mailboxes = list(result.scalars().all())

        renewed = 0
        errors = 0
        for mb in mailboxes:
            try:
                data = await renew_subscription(mb.graph_subscription_id)
                mb.subscription_expiry = data.get("expirationDateTime")
                renewed += 1
            except Exception as e:
                errors += 1

        await db.commit()
        return {"renewed": renewed, "errors": errors, "total": len(mailboxes)}


@app.task(name="workers.tasks.email_tasks.process_email_notification", bind=True,
          max_retries=3, default_retry_delay=10)
def process_email_notification(self, notification_data: dict):
    """Process incoming email from Microsoft Graph webhook."""
    try:
        return _run_async(_process_email_async(notification_data))
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@app.task(name="workers.tasks.email_tasks.send_email", bind=True,
          max_retries=3, default_retry_delay=10)
def send_email(self, tenant_id: str, mailbox_ms_id: str, to: str,
               subject: str, body_html: str, reply_to: str | None = None):
    """Send email via Microsoft Graph API."""
    async def _send():
        from app.modules.email.graph_client import send_mail
        await send_mail(mailbox_ms_id, [to], subject, body_html, reply_to_message_id=reply_to)
        return {"status": "sent", "to": to}

    try:
        return _run_async(_send())
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@app.task(name="workers.tasks.email_tasks.renew_graph_subscriptions", bind=True)
def renew_graph_subscriptions(self):
    """Renew all Microsoft Graph webhook subscriptions before they expire."""
    try:
        return _run_async(_renew_subscriptions_async())
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=2)
