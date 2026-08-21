"""Blocking open items stop the build from inventing a value.

BUILD.md: if a value you need is in spec/open_items.csv, stop and ask.
This module records the stop; it never fills the blank.
"""

from __future__ import annotations

from dataclasses import dataclass

from .spec_loader import open_items


@dataclass(frozen=True)
class OpenItemHalt:
    item_id: str
    subject: str
    detail: str
    blocking: bool
    message: str


def _is_true(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def items() -> list[dict[str, str]]:
    return list(open_items())


def blocking_items() -> list[dict[str, str]]:
    return [row for row in items() if _is_true(row.get("blocking", ""))]


def item_by_id(item_id: str) -> dict[str, str] | None:
    for row in items():
        if row.get("item_id") == item_id:
            return row
    return None


def halt(item_id: str, needed_for: str) -> OpenItemHalt:
    row = item_by_id(item_id)
    if row is None:
        raise KeyError(item_id)
    subject = row.get("subject", "")
    detail = row.get("detail", "")
    blocking = _is_true(row.get("blocking", ""))
    message = (
        f"Open item {item_id} ({subject}) is unsettled. "
        f"Needed for {needed_for}. Do not infer a value."
    )
    if detail:
        message = f"{message} Detail: {detail}"
    return OpenItemHalt(
        item_id=item_id,
        subject=subject,
        detail=detail,
        blocking=blocking,
        message=message,
    )
