"""Jira synchronization service: bidirectional sync with conflict detection."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value
from app.models.jira_config import JiraConfig, JiraSyncLog
from app.models.ticket import Ticket, TicketEvent
from app.modules.jira.client import JiraClient
from app.modules.jira.mapper import map_to_jira, map_from_jira, detect_conflicts


async def get_jira_client(db: AsyncSession, tenant_id: UUID) -> tuple[JiraClient, JiraConfig] | None:
    """Get a configured Jira client for a tenant."""
    result = await db.execute(
        select(JiraConfig).where(
            JiraConfig.tenant_id == tenant_id,
            JiraConfig.sync_enabled == True,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        return None

    api_token = decrypt_value(config.api_token_encrypted)
    client = JiraClient(config.site_url, config.api_email, api_token)
    return client, config


async def sync_ticket_to_jira(db: AsyncSession, ticket: Ticket) -> dict:
    """Sync a ticket to Jira (outbound). Creates or updates."""
    result = await get_jira_client(db, ticket.tenant_id)
    if not result:
        return {"status": "skipped", "reason": "no_jira_config"}

    client, config = result

    # Map fields
    from app.models.project import Project
    project = await db.get(Project, ticket.project_id) if ticket.project_id else None
    jira_project_key = project.jira_project_key if project else None

    if not jira_project_key:
        return {"status": "skipped", "reason": "no_jira_project_key"}

    mapped = map_to_jira(
        {"subject": ticket.subject, "description": ticket.description or "",
         "priority": ticket.priority, "type": ticket.type, "status": ticket.status},
        config.status_mapping, config.priority_mapping,
    )

    try:
        if not ticket.jira_issue_key:
            # Create new issue
            issue = await client.create_issue(
                project_key=jira_project_key,
                summary=mapped["summary"],
                description=mapped["description"],
                issue_type=mapped["issue_type"],
                priority=mapped["priority"],
            )
            ticket.jira_issue_key = issue.get("key")
            ticket.jira_issue_id = issue.get("id")
            ticket.jira_sync_status = "synced"
            action = "create"
        else:
            # Update existing issue
            await client.update_issue(ticket.jira_issue_key, {
                "summary": mapped["summary"],
                "priority": {"name": mapped["priority"]},
            })
            ticket.jira_sync_status = "synced"
            action = "update"

        ticket.jira_last_sync_at = datetime.now(timezone.utc)

        # Log sync
        log = JiraSyncLog(
            tenant_id=ticket.tenant_id,
            ticket_id=ticket.id,
            direction="outbound",
            action=action,
            status="success",
        )
        db.add(log)
        await db.flush()

        return {"status": "success", "action": action, "jira_key": ticket.jira_issue_key}

    except Exception as e:
        ticket.jira_sync_status = "error"
        log = JiraSyncLog(
            tenant_id=ticket.tenant_id,
            ticket_id=ticket.id,
            direction="outbound",
            action="create" if not ticket.jira_issue_key else "update",
            status="failed",
            error_message=str(e),
        )
        db.add(log)
        await db.flush()
        return {"status": "error", "error": str(e)}


async def process_jira_webhook(db: AsyncSession, payload: dict) -> dict:
    """Process an incoming Jira webhook (inbound sync)."""
    event_type = payload.get("webhookEvent", "")
    issue = payload.get("issue", {})
    issue_key = issue.get("key")

    if not issue_key:
        return {"status": "skipped", "reason": "no_issue_key"}

    # Find our ticket
    result = await db.execute(
        select(Ticket).where(Ticket.jira_issue_key == issue_key)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"status": "skipped", "reason": "ticket_not_found"}

    # Get Jira config for mappings
    jira_result = await get_jira_client(db, ticket.tenant_id)
    if not jira_result:
        return {"status": "skipped", "reason": "no_jira_config"}

    _, config = jira_result
    jira_fields = map_from_jira(issue, config.status_mapping, config.priority_mapping)

    # Detect conflicts
    our_data = {"status": ticket.status, "priority": ticket.priority}
    conflicts = detect_conflicts(our_data, jira_fields, str(ticket.jira_last_sync_at))

    if conflicts:
        ticket.jira_sync_status = "conflict"
        event = TicketEvent(
            tenant_id=ticket.tenant_id,
            ticket_id=ticket.id,
            event_type="jira_sync",
            metadata_={"conflict": True, "fields": conflicts, "jira_values": jira_fields},
        )
        db.add(event)
        log = JiraSyncLog(
            tenant_id=ticket.tenant_id, ticket_id=ticket.id,
            direction="inbound", action="update", status="conflict",
            request_payload=payload,
        )
        db.add(log)
        await db.flush()
        return {"status": "conflict", "fields": conflicts}

    # Apply changes (no conflict)
    if "jira:issue_updated" in event_type:
        # Jira is authoritative for assignee
        if jira_fields.get("jira_assignee"):
            event = TicketEvent(
                tenant_id=ticket.tenant_id, ticket_id=ticket.id,
                event_type="jira_sync",
                metadata_={"synced_fields": jira_fields, "direction": "inbound"},
            )
            db.add(event)

    ticket.jira_sync_status = "synced"
    ticket.jira_last_sync_at = datetime.now(timezone.utc)

    log = JiraSyncLog(
        tenant_id=ticket.tenant_id, ticket_id=ticket.id,
        direction="inbound", action="update", status="success",
        request_payload=payload,
    )
    db.add(log)
    await db.flush()

    return {"status": "success", "action": "update"}
