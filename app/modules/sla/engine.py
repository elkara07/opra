"""SLA engine: business hours calculation, timer management, breach detection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
from typing import Optional
from uuid import UUID


# ---------------------------------------------------------------------------
# Business Hours Calculation
# ---------------------------------------------------------------------------

# Day name mapping for business_hours JSONB keys
_DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _parse_time(t: str) -> tuple[int, int]:
    """Parse 'HH:MM' string to (hour, minute)."""
    parts = t.split(":")
    return int(parts[0]), int(parts[1])


def calculate_business_minutes(
    start: datetime,
    end: datetime,
    business_hours: dict,
    holidays: list[dict] | None = None,
    tz: str = "UTC",
) -> int:
    """Calculate elapsed business-hours minutes between two datetimes.

    Args:
        start: Start datetime (timezone-aware or naive UTC)
        end: End datetime (timezone-aware or naive UTC)
        business_hours: {"mon": {"start": "09:00", "end": "18:00"}, ...}
        holidays: [{"date": "2026-12-25"}, ...]
        tz: Tenant timezone (e.g., "Europe/Istanbul")

    Returns:
        Total minutes within business hours between start and end.
    """
    if not business_hours:
        # No business hours configured = 24/7 operation
        return int((end - start).total_seconds() / 60)

    zone = ZoneInfo(tz)

    # Convert to tenant timezone
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    current = start.astimezone(zone)
    end_tz = end.astimezone(zone)

    if current >= end_tz:
        return 0

    holiday_dates = set()
    if holidays:
        for h in holidays:
            d = h.get("date", "")
            if d:
                holiday_dates.add(d)

    total_minutes = 0

    # Iterate day by day
    while current < end_tz:
        day_idx = current.weekday()  # 0=Monday
        day_key = _DAY_KEYS[day_idx]
        date_str = current.strftime("%Y-%m-%d")

        day_config = business_hours.get(day_key)

        if day_config and date_str not in holiday_dates:
            bh_start_h, bh_start_m = _parse_time(day_config["start"])
            bh_end_h, bh_end_m = _parse_time(day_config["end"])

            bh_start = current.replace(
                hour=bh_start_h, minute=bh_start_m, second=0, microsecond=0,
            )
            bh_end = current.replace(
                hour=bh_end_h, minute=bh_end_m, second=0, microsecond=0,
            )

            effective_start = max(current, bh_start)
            effective_end = min(end_tz, bh_end)

            if effective_start < effective_end:
                delta = (effective_end - effective_start).total_seconds() / 60
                total_minutes += delta

        # Move to start of next day
        current = (current + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )

    return int(total_minutes)


def calculate_due_date(
    start: datetime,
    minutes: int,
    business_hours: dict,
    holidays: list[dict] | None = None,
    tz: str = "UTC",
) -> datetime:
    """Calculate when a SLA deadline falls, counting only business hours.

    Args:
        start: When the SLA clock started
        minutes: SLA target in business minutes
        business_hours: Tenant's business hours config
        holidays: Tenant's holiday list
        tz: Tenant timezone

    Returns:
        The datetime when the SLA will be breached (timezone-aware UTC).
    """
    if not business_hours:
        # 24/7 operation
        return start + timedelta(minutes=minutes)

    zone = ZoneInfo(tz)

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    current = start.astimezone(zone)
    remaining = minutes

    holiday_dates = set()
    if holidays:
        for h in holidays:
            d = h.get("date", "")
            if d:
                holiday_dates.add(d)

    max_iterations = minutes + 365 * 24 * 60  # Safety limit
    iteration = 0

    while remaining > 0 and iteration < max_iterations:
        iteration += 1
        day_idx = current.weekday()
        day_key = _DAY_KEYS[day_idx]
        date_str = current.strftime("%Y-%m-%d")

        day_config = business_hours.get(day_key)

        if day_config and date_str not in holiday_dates:
            bh_start_h, bh_start_m = _parse_time(day_config["start"])
            bh_end_h, bh_end_m = _parse_time(day_config["end"])

            bh_start = current.replace(
                hour=bh_start_h, minute=bh_start_m, second=0, microsecond=0,
            )
            bh_end = current.replace(
                hour=bh_end_h, minute=bh_end_m, second=0, microsecond=0,
            )

            effective_start = max(current, bh_start)

            if effective_start < bh_end:
                available = (bh_end - effective_start).total_seconds() / 60

                if remaining <= available:
                    # SLA deadline falls within this day
                    due = effective_start + timedelta(minutes=remaining)
                    return due.astimezone(timezone.utc)
                else:
                    remaining -= available

        # Move to start of next day
        current = (current + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )

    # Fallback: if we somehow exhaust iterations
    return current.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# SLA Status Evaluation
# ---------------------------------------------------------------------------

def evaluate_sla_status(
    created_at: datetime,
    sla_response_due: datetime | None,
    sla_resolution_due: datetime | None,
    sla_responded_at: datetime | None,
    sla_resolved_at: datetime | None,
    sla_paused_at: datetime | None,
    now: datetime | None = None,
) -> dict:
    """Evaluate current SLA status for a ticket.

    Returns:
        {
            "response": {"status": "ok"|"warning"|"breached", "remaining_minutes": int, "pct": float},
            "resolution": {"status": "ok"|"warning"|"breached", "remaining_minutes": int, "pct": float},
        }
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result = {}

    for sla_type, due, completed_at in [
        ("response", sla_response_due, sla_responded_at),
        ("resolution", sla_resolution_due, sla_resolved_at),
    ]:
        if due is None:
            result[sla_type] = {"status": "not_configured", "remaining_minutes": None, "pct": 0}
            continue

        if completed_at:
            if completed_at <= due:
                result[sla_type] = {"status": "met", "remaining_minutes": 0, "pct": 100}
            else:
                result[sla_type] = {"status": "breached", "remaining_minutes": 0, "pct": 100}
            continue

        # SLA is paused
        if sla_paused_at:
            remaining = (due - sla_paused_at).total_seconds() / 60
        else:
            remaining = (due - now).total_seconds() / 60

        total = (due - created_at).total_seconds() / 60
        elapsed_pct = ((total - remaining) / total * 100) if total > 0 else 0

        if remaining <= 0:
            status = "breached"
        elif elapsed_pct >= 80:
            status = "warning"
        else:
            status = "ok"

        result[sla_type] = {
            "status": status,
            "remaining_minutes": max(0, int(remaining)),
            "pct": round(min(100, elapsed_pct), 1),
        }

    return result
