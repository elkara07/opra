"""Jira Cloud REST API v3 async client."""

from __future__ import annotations

import base64

import httpx


class JiraClient:
    """Thin async wrapper around Jira Cloud REST API v3."""

    def __init__(self, site_url: str, api_email: str, api_token: str):
        self.base_url = f"https://{site_url}/rest/api/3"
        self._auth = base64.b64encode(f"{api_email}:{api_token}".encode()).decode()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await client.request(method, url, headers=self._headers(), **kwargs)

    # --- Issues ---

    async def create_issue(self, project_key: str, summary: str, description: str,
                           issue_type: str = "Task", priority: str = "Medium",
                           **extra_fields) -> dict:
        """Create a Jira issue."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
                **extra_fields,
            }
        }
        resp = await self._request("POST", "/issue", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_issue(self, issue_key: str, fields: dict) -> None:
        """Update issue fields."""
        payload = {"fields": fields}
        resp = await self._request("PUT", f"/issue/{issue_key}", json=payload)
        resp.raise_for_status()

    async def get_issue(self, issue_key: str) -> dict:
        """Get issue details."""
        resp = await self._request("GET", f"/issue/{issue_key}")
        resp.raise_for_status()
        return resp.json()

    async def transition_issue(self, issue_key: str, transition_name: str) -> bool:
        """Transition issue to a new status."""
        # Get available transitions
        resp = await self._request("GET", f"/issue/{issue_key}/transitions")
        resp.raise_for_status()
        transitions = resp.json().get("transitions", [])

        target = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                target = t
                break

        if not target:
            return False

        payload = {"transition": {"id": target["id"]}}
        resp = await self._request("POST", f"/issue/{issue_key}/transitions", json=payload)
        resp.raise_for_status()
        return True

    async def add_comment(self, issue_key: str, body: str) -> dict:
        """Add a comment to an issue."""
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}],
            }
        }
        resp = await self._request("POST", f"/issue/{issue_key}/comment", json=payload)
        resp.raise_for_status()
        return resp.json()

    # --- Health ---

    async def test_connection(self) -> dict:
        """Test Jira connectivity."""
        resp = await self._request("GET", "/myself")
        resp.raise_for_status()
        return resp.json()
