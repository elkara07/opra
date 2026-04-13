"""Notification dispatch tasks."""

from __future__ import annotations

from workers.celery_app import app


@app.task(name="workers.tasks.notification_tasks.send_notification", bind=True, max_retries=3,
          default_retry_delay=10)
def send_notification(self, tenant_id: str, channel: str, recipient: str,
                      subject: str, body: str, ticket_id: str | None = None):
    """Send a notification via the specified channel.

    Channels: email, sms, webhook
    Logs to notification_log table.
    """
    # TODO: Implement in Faz 2
    pass


@app.task(name="workers.tasks.notification_tasks.notify_stale_tickets", bind=True)
def notify_stale_tickets(self):
    """Find tickets with no update for configurable period and alert assigned agents."""
    # TODO: Implement in Faz 2
    pass
