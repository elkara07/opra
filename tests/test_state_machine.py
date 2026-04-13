"""Tests for ticket state machine transitions."""

import pytest

from app.models.ticket import TICKET_TRANSITIONS, TICKET_STATUSES, TICKET_TYPES, TICKET_PRIORITIES


class TestTicketTypes:
    def test_four_itil_types(self):
        assert len(TICKET_TYPES) == 4
        assert "incident" in TICKET_TYPES
        assert "service_request" in TICKET_TYPES
        assert "problem" in TICKET_TYPES
        assert "change" in TICKET_TYPES


class TestTicketStatuses:
    def test_eight_statuses(self):
        assert len(TICKET_STATUSES) == 8

    def test_all_statuses_have_transitions(self):
        for status in TICKET_STATUSES:
            assert status in TICKET_TRANSITIONS, f"{status} missing from transitions"


class TestTicketPriorities:
    def test_four_priorities(self):
        assert TICKET_PRIORITIES == ("P1", "P2", "P3", "P4")


class TestTransitions:
    def test_new_can_go_to_assigned(self):
        assert "assigned" in TICKET_TRANSITIONS["new"]

    def test_new_can_go_to_in_progress(self):
        assert "in_progress" in TICKET_TRANSITIONS["new"]

    def test_new_can_be_cancelled(self):
        assert "cancelled" in TICKET_TRANSITIONS["new"]

    def test_in_progress_to_pending(self):
        assert "pending_customer" in TICKET_TRANSITIONS["in_progress"]
        assert "pending_vendor" in TICKET_TRANSITIONS["in_progress"]

    def test_in_progress_to_resolved(self):
        assert "resolved" in TICKET_TRANSITIONS["in_progress"]

    def test_resolved_can_reopen(self):
        assert "in_progress" in TICKET_TRANSITIONS["resolved"]

    def test_resolved_can_close(self):
        assert "closed" in TICKET_TRANSITIONS["resolved"]

    def test_closed_is_terminal(self):
        assert len(TICKET_TRANSITIONS["closed"]) == 0

    def test_cancelled_is_terminal(self):
        assert len(TICKET_TRANSITIONS["cancelled"]) == 0

    def test_pending_customer_resumes(self):
        assert "in_progress" in TICKET_TRANSITIONS["pending_customer"]

    def test_no_invalid_targets(self):
        for src, targets in TICKET_TRANSITIONS.items():
            for t in targets:
                assert t in TICKET_STATUSES, f"Invalid target: {src} -> {t}"

    def test_cannot_go_from_new_to_closed_directly(self):
        assert "closed" not in TICKET_TRANSITIONS["new"]

    def test_cannot_go_from_new_to_resolved_directly(self):
        assert "resolved" not in TICKET_TRANSITIONS["new"]


class TestJiraMapper:
    def test_priority_mapping(self):
        from app.modules.jira.mapper import map_to_jira
        mapped = map_to_jira({"priority": "P1", "subject": "x", "type": "incident", "status": "new"})
        assert mapped["priority"] == "Highest"

    def test_type_mapping(self):
        from app.modules.jira.mapper import map_to_jira
        mapped = map_to_jira({"priority": "P3", "subject": "x", "type": "service_request", "status": "new"})
        assert mapped["issue_type"] == "Task"

    def test_conflict_detection_same_values(self):
        from app.modules.jira.mapper import detect_conflicts
        conflicts = detect_conflicts({"status": "in_progress", "priority": "P2"},
                                     {"status": "in_progress", "priority": "P2"}, None)
        assert len(conflicts) == 0

    def test_conflict_detection_different_status(self):
        from app.modules.jira.mapper import detect_conflicts
        conflicts = detect_conflicts({"status": "in_progress", "priority": "P2"},
                                     {"status": "resolved", "priority": "P2"}, None)
        assert "status" in conflicts
        assert "priority" not in conflicts
