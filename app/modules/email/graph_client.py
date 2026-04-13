"""Microsoft Graph API client for email operations."""

from __future__ import annotations

import httpx
import msal

from app.core.config import settings

# Token cache (in-memory, single process)
_token_cache: dict[str, str] = {}


async def _get_access_token() -> str:
    """Get an app-only access token for Microsoft Graph using MSAL."""
    cache_key = "graph_token"
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    authority = f"https://login.microsoftonline.com/{settings.ms_graph_tenant_id}"
    app = msal.ConfidentialClientApplication(
        settings.ms_graph_client_id,
        authority=authority,
        client_credential=settings.ms_graph_client_secret,
    )

    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Failed to acquire Graph token: {result.get('error_description')}")

    _token_cache[cache_key] = result["access_token"]
    return result["access_token"]


def _clear_token_cache():
    """Clear cached token (e.g., on 401 response)."""
    _token_cache.clear()


async def _graph_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Make an authenticated request to Microsoft Graph API."""
    token = await _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401:
            _clear_token_cache()
            # Retry once with fresh token
            token = await _get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            response = await client.request(method, url, headers=headers, **kwargs)
        return response


# ---------------------------------------------------------------------------
# Email operations
# ---------------------------------------------------------------------------

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


async def get_message(mailbox_id: str, message_id: str) -> dict:
    """Fetch a full email message with attachments metadata."""
    url = f"{GRAPH_BASE}/users/{mailbox_id}/messages/{message_id}"
    params = {"$expand": "attachments", "$select": (
        "id,conversationId,internetMessageId,subject,bodyPreview,"
        "body,from,toRecipients,ccRecipients,hasAttachments,"
        "receivedDateTime,sentDateTime,internetMessageHeaders,"
        "isReadReceiptRequested,inferenceClassification"
    )}
    response = await _graph_request("GET", url, params=params)
    response.raise_for_status()
    return response.json()


async def download_attachment(mailbox_id: str, message_id: str, attachment_id: str) -> bytes:
    """Download an attachment's raw content."""
    url = f"{GRAPH_BASE}/users/{mailbox_id}/messages/{message_id}/attachments/{attachment_id}/$value"
    response = await _graph_request("GET", url)
    response.raise_for_status()
    return response.content


async def send_mail(mailbox_id: str, to: list[str], subject: str, body_html: str,
                    cc: list[str] | None = None, reply_to_message_id: str | None = None):
    """Send an email from a shared mailbox via Graph API."""
    message = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": body_html},
        "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
    }
    if cc:
        message["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]

    if reply_to_message_id:
        # Reply to existing message (maintains threading)
        url = f"{GRAPH_BASE}/users/{mailbox_id}/messages/{reply_to_message_id}/reply"
        payload = {"message": message}
    else:
        url = f"{GRAPH_BASE}/users/{mailbox_id}/sendMail"
        payload = {"message": message, "saveToSentItems": True}

    response = await _graph_request("POST", url, json=payload)
    response.raise_for_status()


# ---------------------------------------------------------------------------
# Webhook subscription management
# ---------------------------------------------------------------------------

async def create_subscription(mailbox_id: str, webhook_url: str, client_state: str) -> dict:
    """Create a Graph API change notification subscription for a mailbox."""
    url = f"{GRAPH_BASE}/subscriptions"
    payload = {
        "changeType": "created",
        "notificationUrl": webhook_url,
        "resource": f"/users/{mailbox_id}/mailFolders/Inbox/messages",
        "expirationDateTime": None,  # Will be set by Graph (max ~4230 min)
        "clientState": client_state,
    }
    # Calculate max expiry (Graph allows ~3 days for mail)
    from datetime import datetime, timedelta, timezone
    expiry = datetime.now(timezone.utc) + timedelta(minutes=4200)
    payload["expirationDateTime"] = expiry.isoformat()

    response = await _graph_request("POST", url, json=payload)
    response.raise_for_status()
    return response.json()


async def renew_subscription(subscription_id: str) -> dict:
    """Renew an existing subscription before it expires."""
    url = f"{GRAPH_BASE}/subscriptions/{subscription_id}"
    from datetime import datetime, timedelta, timezone
    expiry = datetime.now(timezone.utc) + timedelta(minutes=4200)
    payload = {"expirationDateTime": expiry.isoformat()}
    response = await _graph_request("PATCH", url, json=payload)
    response.raise_for_status()
    return response.json()


async def delete_subscription(subscription_id: str):
    """Delete a webhook subscription."""
    url = f"{GRAPH_BASE}/subscriptions/{subscription_id}"
    response = await _graph_request("DELETE", url)
    # 204 = success, 404 = already deleted
    if response.status_code not in (204, 404):
        response.raise_for_status()
