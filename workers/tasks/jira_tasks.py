"""Jira synchronization tasks."""

from __future__ import annotations

from workers.celery_app import app


@app.task(name="workers.tasks.jira_tasks.sync_ticket_to_jira", bind=True, max_retries=3,
          default_retry_delay=30)
def sync_ticket_to_jira(self, ticket_id: str):
    """Create or update a Jira issue from a local ticket.

    1. Load ticket + tenant jira_config
    2. Map fields (status, priority, description)
    3. If no jira_issue_key: POST create issue
    4. If jira_issue_key exists: PUT update issue
    5. Update ticket.jira_sync_status
    6. Log to jira_sync_log
    """
    # TODO: Implement in Faz 3
    pass


@app.task(name="workers.tasks.jira_tasks.retry_failed_syncs", bind=True)
def retry_failed_syncs(self):
    """Re-attempt failed Jira syncs (jira_sync_status='error')."""
    # TODO: Implement in Faz 3
    pass
