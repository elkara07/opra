"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def business_hours():
    """Standard Mon-Fri 09:00-18:00 business hours."""
    return {
        "mon": {"start": "09:00", "end": "18:00"},
        "tue": {"start": "09:00", "end": "18:00"},
        "wed": {"start": "09:00", "end": "18:00"},
        "thu": {"start": "09:00", "end": "18:00"},
        "fri": {"start": "09:00", "end": "18:00"},
    }


@pytest.fixture
def holidays():
    """Sample holiday list."""
    return [
        {"date": "2026-01-01", "name": "New Year"},
        {"date": "2026-04-23", "name": "National Sovereignty Day"},
        {"date": "2026-05-01", "name": "Labor Day"},
    ]


@pytest.fixture
def sample_graph_message():
    """Sample Microsoft Graph API email message."""
    return {
        "id": "AAMkAGI2TG93AAA=",
        "conversationId": "AAQkAGI2TG93AAA=",
        "internetMessageId": "<msg-001@company.com>",
        "from": {
            "emailAddress": {"address": "user@customer.com", "name": "John Doe"}
        },
        "toRecipients": [
            {"emailAddress": {"address": "support@ops.com"}}
        ],
        "ccRecipients": [],
        "subject": "Server is down - urgent",
        "body": {
            "contentType": "html",
            "content": "<html><body><p>Our production server has been unresponsive since 10:00 AM.</p><p>Please help ASAP.</p></body></html>",
        },
        "hasAttachments": False,
        "attachments": [],
        "internetMessageHeaders": [
            {"name": "In-Reply-To", "value": ""},
        ],
        "receivedDateTime": "2026-04-13T10:05:00Z",
        "sentDateTime": "2026-04-13T10:04:30Z",
        "inferenceClassification": "focused",
    }
