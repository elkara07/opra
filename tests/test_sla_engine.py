"""Tests for SLA engine: business hours calculation and due date."""

from datetime import datetime, timezone, timedelta

import pytest

from app.modules.sla.engine import (
    calculate_business_minutes,
    calculate_due_date,
    evaluate_sla_status,
)


class TestBusinessMinutes:
    def test_same_day_within_hours(self, business_hours):
        start = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc)
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 120

    def test_weekend_zero(self, business_hours):
        start = datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc)  # Saturday
        end = datetime(2026, 4, 12, 18, 0, tzinfo=timezone.utc)    # Sunday
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 0

    def test_cross_weekend(self, business_hours):
        start = datetime(2026, 4, 10, 16, 0, tzinfo=timezone.utc)  # Fri
        end = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)    # Mon
        # Fri 16-18=120 + Mon 09-10=60 = 180
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 180

    def test_full_business_day(self, business_hours):
        start = datetime(2026, 4, 13, 0, 0, tzinfo=timezone.utc)   # Mon 00:00
        end = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)     # Tue 00:00
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 540  # 9h

    def test_holiday_excluded(self, business_hours):
        holidays = [{"date": "2026-04-13"}]
        start = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 18, 0, tzinfo=timezone.utc)
        assert calculate_business_minutes(start, end, business_hours, holidays, tz="UTC") == 0

    def test_24_7_mode(self):
        start = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc)
        assert calculate_business_minutes(start, end, {}, tz="UTC") == 120

    def test_before_business_hours(self, business_hours):
        start = datetime(2026, 4, 13, 6, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        # Only 09-10 counts = 60
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 60

    def test_after_business_hours(self, business_hours):
        start = datetime(2026, 4, 13, 19, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 22, 0, tzinfo=timezone.utc)
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 0

    def test_end_before_start_returns_zero(self, business_hours):
        start = datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        assert calculate_business_minutes(start, end, business_hours, tz="UTC") == 0


class TestDueDate:
    def test_simple_within_day(self, business_hours):
        start = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        due = calculate_due_date(start, 15, business_hours, tz="UTC")
        assert due == datetime(2026, 4, 13, 9, 15, tzinfo=timezone.utc)

    def test_overnight_rollover(self, business_hours):
        start = datetime(2026, 4, 13, 17, 50, tzinfo=timezone.utc)
        due = calculate_due_date(start, 30, business_hours, tz="UTC")
        # 10 min left on Mon, 20 min on Tue -> Tue 09:20
        assert due == datetime(2026, 4, 14, 9, 20, tzinfo=timezone.utc)

    def test_weekend_skip(self, business_hours):
        start = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)  # Fri
        due = calculate_due_date(start, 120, business_hours, tz="UTC")
        # Fri 17-18=60, Mon 09-10=60 -> Mon 10:00
        assert due == datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)

    def test_p1_response_time(self, business_hours):
        """P1 = 15 min response, should be within same day."""
        start = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        due = calculate_due_date(start, 15, business_hours, tz="UTC")
        assert due == datetime(2026, 4, 13, 14, 15, tzinfo=timezone.utc)

    def test_p4_resolution_multi_day(self, business_hours):
        """P4 = 5760 min (96h business) = ~10.6 business days."""
        start = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)  # Mon
        due = calculate_due_date(start, 5760, business_hours, tz="UTC")
        # 5760 / 540 per day = 10.67 days -> ~2 weeks + 1 day
        assert due > start + timedelta(days=10)

    def test_24_7_mode(self):
        start = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        due = calculate_due_date(start, 120, {}, tz="UTC")
        assert due == start + timedelta(minutes=120)


class TestSLAStatus:
    def test_response_breached(self):
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        created = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        response_due = datetime(2026, 4, 13, 9, 15, tzinfo=timezone.utc)

        status = evaluate_sla_status(created, response_due, None, None, None, None, now)
        assert status["response"]["status"] == "breached"

    def test_response_met(self):
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        created = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        response_due = datetime(2026, 4, 13, 9, 15, tzinfo=timezone.utc)
        responded = datetime(2026, 4, 13, 9, 10, tzinfo=timezone.utc)

        status = evaluate_sla_status(created, response_due, None, responded, None, None, now)
        assert status["response"]["status"] == "met"

    def test_warning_at_80_percent(self):
        created = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        response_due = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)  # 60 min
        now = datetime(2026, 4, 13, 9, 50, tzinfo=timezone.utc)  # 50/60 = 83%

        status = evaluate_sla_status(created, response_due, None, None, None, None, now)
        assert status["response"]["status"] == "warning"

    def test_paused_sla(self):
        created = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        response_due = datetime(2026, 4, 13, 9, 15, tzinfo=timezone.utc)
        paused_at = datetime(2026, 4, 13, 9, 10, tzinfo=timezone.utc)
        now = datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc)

        status = evaluate_sla_status(created, response_due, None, None, None, paused_at, now)
        assert status["response"]["remaining_minutes"] > 0  # Clock frozen at pause time

    def test_not_configured(self):
        created = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        status = evaluate_sla_status(created, None, None, None, None, None)
        assert status["response"]["status"] == "not_configured"
