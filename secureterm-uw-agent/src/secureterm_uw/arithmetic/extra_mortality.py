"""Deterministic Extra Mortality parsing. Never a model call."""

from __future__ import annotations

import re

_EM = re.compile(r"(-?\d+(?:\.\d+)?)\s*%?")


def parse_em_percent(raw: str | float | int | None) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    match = _EM.search(str(raw))
    if not match:
        return None
    return float(match.group(1))


GENERIC_OVERRIDE_REASONS = {
    "",
    "override",
    "n/a",
    "na",
    "none",
    "yes",
    ".",
    "-",
}


def override_reason_is_valid(reason: str | None) -> bool:
    if reason is None:
        return False
    cleaned = " ".join(reason.strip().lower().split())
    if cleaned in GENERIC_OVERRIDE_REASONS:
        return False
    return len(cleaned) >= 8
