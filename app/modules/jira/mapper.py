"""Jira field mapping: our system <-> Jira Cloud."""

from __future__ import annotations


# Default status mapping: our_status -> Jira status name
DEFAULT_STATUS_MAP = {
    "new": "To Do",
    "assigned": "To Do",
    "in_progress": "In Progress",
    "pending_customer": "Waiting for Customer",
    "pending_vendor": "Waiting for Support",
    "resolved": "Done",
    "closed": "Done",
    "cancelled": "Cancelled",
}

# Default priority mapping: our_priority -> Jira priority name
DEFAULT_PRIORITY_MAP = {
    "P1": "Highest",
    "P2": "High",
    "P3": "Medium",
    "P4": "Low",
}

# Reverse mappings (Jira -> ours)
DEFAULT_STATUS_REVERSE = {v: k for k, v in DEFAULT_STATUS_MAP.items()}
DEFAULT_PRIORITY_REVERSE = {v: k for k, v in DEFAULT_PRIORITY_MAP.items()}

# Default type mapping
DEFAULT_TYPE_MAP = {
    "incident": "Bug",
    "service_request": "Task",
    "problem": "Bug",
    "change": "Story",
}


def map_to_jira(ticket: dict, status_map: dict | None = None,
                priority_map: dict | None = None, type_map: dict | None = None) -> dict:
    """Map our ticket fields to Jira issue fields."""
    s_map = status_map or DEFAULT_STATUS_MAP
    p_map = priority_map or DEFAULT_PRIORITY_MAP
    t_map = type_map or DEFAULT_TYPE_MAP

    return {
        "summary": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
        "priority": p_map.get(ticket.get("priority", "P3"), "Medium"),
        "issue_type": t_map.get(ticket.get("type", "incident"), "Task"),
        "status": s_map.get(ticket.get("status", "new"), "To Do"),
    }


def map_from_jira(jira_issue: dict, status_map: dict | None = None,
                  priority_map: dict | None = None) -> dict:
    """Map Jira issue fields back to our ticket fields."""
    s_map = status_map or DEFAULT_STATUS_REVERSE
    p_map = priority_map or DEFAULT_PRIORITY_REVERSE

    fields = jira_issue.get("fields", {})
    jira_status = fields.get("status", {}).get("name", "")
    jira_priority = fields.get("priority", {}).get("name", "")

    return {
        "subject": fields.get("summary", ""),
        "status": s_map.get(jira_status, "in_progress"),
        "priority": p_map.get(jira_priority, "P3"),
        "jira_assignee": (fields.get("assignee") or {}).get("displayName"),
    }


def detect_conflicts(our_ticket: dict, jira_fields: dict,
                     our_last_sync: str | None) -> list[str]:
    """Detect fields changed on both sides since last sync.

    Returns list of conflicting field names.
    """
    conflicts = []

    # We only check status and priority for conflicts
    # (description conflicts are resolved by last-write-wins)
    for field in ("status", "priority"):
        our_val = our_ticket.get(field)
        jira_val = jira_fields.get(field)
        if our_val and jira_val and our_val != jira_val:
            conflicts.append(field)

    return conflicts
