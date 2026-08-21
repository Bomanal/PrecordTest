"""In-memory run history for the dashboard."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any

_RUNS: deque[dict[str, Any]] = deque(maxlen=100)


def record(entry: dict[str, Any]) -> None:
    item = dict(entry)
    item.setdefault("recorded_at", datetime.now(UTC).isoformat())
    _RUNS.appendleft(item)


def recent(limit: int = 25) -> list[dict[str, Any]]:
    return list(_RUNS)[:limit]


def clear() -> None:
    _RUNS.clear()
