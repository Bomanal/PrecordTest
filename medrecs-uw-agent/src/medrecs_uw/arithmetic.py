"""Deterministic arithmetic — never a model call."""

from __future__ import annotations

from datetime import datetime

ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def cycle_time_hours(received_at: str | None, bound_at: str | None) -> float | None:
    start = parse_timestamp(received_at)
    end = parse_timestamp(bound_at)
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 3600.0, 2)


def parse_aging_hours(aging: str | None) -> float | None:
    """Parse a display aging string. Returns None rather than inventing a unit."""
    if not aging:
        return None
    text = aging.strip().lower()
    parts = text.replace(",", " ").split()
    if not parts:
        return None
    try:
        amount = float(parts[0])
    except ValueError:
        return None
    unit = parts[1] if len(parts) > 1 else "days"
    if unit.startswith("hour"):
        return amount
    if unit.startswith("day"):
        return amount * 24.0
    if unit.startswith("week"):
        return amount * 24.0 * 7.0
    return None
