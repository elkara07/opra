"""Tests for email parsing module."""

import pytest

from app.modules.email.parser import (
    extract_ticket_number,
    html_to_text,
    is_auto_reply,
    parse_graph_message,
)


class TestTicketNumberExtraction:
    def test_standard_format(self):
        assert extract_ticket_number("Re: Server down [TKT-00042]") == "TKT-00042"

    def test_in_middle(self):
        assert extract_ticket_number("FW: [TKT-00001] Issue report") == "TKT-00001"

    def test_no_ticket(self):
        assert extract_ticket_number("New support request") is None

    def test_empty_subject(self):
        assert extract_ticket_number("") is None

    def test_none_subject(self):
        assert extract_ticket_number(None) is None

    def test_similar_but_wrong_format(self):
        assert extract_ticket_number("[TKT-123]") is None  # Not 5 digits
        assert extract_ticket_number("TKT-00042") is None  # No brackets


class TestHtmlToText:
    def test_basic_html(self):
        text = html_to_text("<p>Hello</p><p>World</p>")
        assert "Hello" in text
        assert "World" in text

    def test_strips_scripts(self):
        text = html_to_text("<p>OK</p><script>alert(1)</script>")
        assert "alert" not in text
        assert "OK" in text

    def test_strips_styles(self):
        text = html_to_text("<style>.red{color:red}</style><p>Content</p>")
        assert "red" not in text
        assert "Content" in text

    def test_empty_html(self):
        assert html_to_text("") == ""

    def test_plain_text_passthrough(self):
        assert "Hello" in html_to_text("Hello")


class TestAutoReplyDetection:
    def test_auto_submitted_header(self):
        msg = {"internetMessageHeaders": [{"name": "Auto-Submitted", "value": "auto-replied"}], "subject": ""}
        assert is_auto_reply(msg) is True

    def test_auto_submitted_no(self):
        msg = {"internetMessageHeaders": [{"name": "Auto-Submitted", "value": "no"}], "subject": ""}
        assert is_auto_reply(msg) is False

    def test_out_of_office_subject_en(self):
        msg = {"internetMessageHeaders": [], "subject": "Out of office: Re: Meeting"}
        assert is_auto_reply(msg) is True

    def test_out_of_office_subject_tr(self):
        msg = {"internetMessageHeaders": [], "subject": "Otomatik yanıt: Toplantı"}
        assert is_auto_reply(msg) is True

    def test_normal_email(self):
        msg = {"internetMessageHeaders": [], "subject": "Need help with login"}
        assert is_auto_reply(msg) is False

    def test_x_auto_response_suppress(self):
        msg = {"internetMessageHeaders": [{"name": "X-Auto-Response-Suppress", "value": "All"}], "subject": ""}
        assert is_auto_reply(msg) is True


class TestParseGraphMessage:
    def test_full_parse(self, sample_graph_message):
        parsed = parse_graph_message(sample_graph_message)

        assert parsed["message_id"] == "AAMkAGI2TG93AAA="
        assert parsed["conversation_id"] == "AAQkAGI2TG93AAA="
        assert parsed["from_address"] == "user@customer.com"
        assert parsed["from_name"] == "John Doe"
        assert parsed["to_addresses"] == ["support@ops.com"]
        assert "production server" in parsed["body_text"]
        assert parsed["has_attachments"] is False
        assert parsed["is_auto_reply"] is False
        assert parsed["ticket_number"] is None  # No ticket number in subject

    def test_reply_with_ticket(self):
        msg = {
            "id": "msg2",
            "conversationId": "conv2",
            "from": {"emailAddress": {"address": "user@test.com", "name": "User"}},
            "toRecipients": [{"emailAddress": {"address": "support@ops.com"}}],
            "ccRecipients": [],
            "subject": "Re: Server down [TKT-00042]",
            "body": {"contentType": "html", "content": "<p>Still broken</p>"},
            "hasAttachments": False,
            "attachments": [],
            "internetMessageHeaders": [{"name": "In-Reply-To", "value": "prev-msg-id"}],
            "receivedDateTime": "2026-04-13T11:00:00Z",
            "sentDateTime": "2026-04-13T10:59:00Z",
        }
        parsed = parse_graph_message(msg)
        assert parsed["ticket_number"] == "TKT-00042"
        assert parsed["in_reply_to"] == "prev-msg-id"
