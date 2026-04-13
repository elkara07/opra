"""Email parsing utilities: extract info from Graph API message."""

from __future__ import annotations

import re
from bs4 import BeautifulSoup


# Pattern for ticket number in subject line: [TKT-00042]
TICKET_PATTERN = re.compile(r"\[TKT-(\d{5})\]")

# Auto-reply detection headers
AUTO_REPLY_HEADERS = {
    "X-Auto-Response-Suppress",
    "Auto-Submitted",
    "X-Autoreply",
    "X-Autorespond",
}


def extract_ticket_number(subject: str) -> str | None:
    """Extract ticket number from email subject if present.

    Returns 'TKT-00042' or None.
    """
    match = TICKET_PATTERN.search(subject or "")
    if match:
        return f"TKT-{match.group(1)}"
    return None


def html_to_text(html: str) -> str:
    """Convert HTML email body to plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for element in soup(["script", "style", "head"]):
        element.decompose()
    text = soup.get_text(separator="\n")
    # Collapse multiple newlines
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def is_auto_reply(message: dict) -> bool:
    """Detect if a Graph API message is an auto-reply/OOO/bounce.

    Args:
        message: Full Graph API message object
    """
    # Check inference classification
    if message.get("inferenceClassification") == "other":
        pass  # Not definitive

    # Check internet message headers
    headers = message.get("internetMessageHeaders", [])
    for h in headers:
        name = h.get("name", "")
        value = h.get("value", "")
        if name == "Auto-Submitted":
            if value and value.lower() != "no":
                return True
            continue
        if name == "X-Auto-Response-Suppress" and value:
            return True
        if name in ("X-Autoreply", "X-Autorespond") and value:
            return True

    # Check subject patterns
    subject = (message.get("subject") or "").lower()
    auto_patterns = [
        "automatic reply:", "out of office:",
        "otomatik yanıt:", "dışarıdayım:",
        "automatische antwort:", "réponse automatique:",
    ]
    for pattern in auto_patterns:
        if subject.startswith(pattern):
            return True

    return False


def parse_graph_message(message: dict) -> dict:
    """Parse a Graph API message into a structured dict.

    Returns:
        {
            "message_id": str,
            "conversation_id": str,
            "from_address": str,
            "from_name": str,
            "to_addresses": [str],
            "cc_addresses": [str],
            "subject": str,
            "body_text": str,
            "body_html": str,
            "has_attachments": bool,
            "attachments": [{"id": str, "name": str, "size": int, "content_type": str}],
            "in_reply_to": str | None,
            "received_at": str,
            "sent_at": str,
            "is_auto_reply": bool,
            "ticket_number": str | None,
        }
    """
    from_obj = message.get("from", {}).get("emailAddress", {})
    body = message.get("body", {})
    body_html = body.get("content", "") if body.get("contentType") == "html" else ""
    body_text = html_to_text(body_html) if body_html else body.get("content", "")

    # Extract in-reply-to from internet headers
    in_reply_to = None
    headers = message.get("internetMessageHeaders", [])
    for h in headers:
        if h.get("name", "").lower() == "in-reply-to":
            in_reply_to = h.get("value")
            break

    attachments = []
    for att in message.get("attachments", []):
        if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
            attachments.append({
                "id": att.get("id"),
                "name": att.get("name"),
                "size": att.get("size", 0),
                "content_type": att.get("contentType"),
            })

    subject = message.get("subject", "")

    return {
        "message_id": message.get("id"),
        "conversation_id": message.get("conversationId"),
        "from_address": from_obj.get("address", ""),
        "from_name": from_obj.get("name", ""),
        "to_addresses": [
            r.get("emailAddress", {}).get("address", "")
            for r in message.get("toRecipients", [])
        ],
        "cc_addresses": [
            r.get("emailAddress", {}).get("address", "")
            for r in message.get("ccRecipients", [])
        ],
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "has_attachments": message.get("hasAttachments", False),
        "attachments": attachments,
        "in_reply_to": in_reply_to,
        "received_at": message.get("receivedDateTime"),
        "sent_at": message.get("sentDateTime"),
        "is_auto_reply": is_auto_reply(message),
        "ticket_number": extract_ticket_number(subject),
    }
