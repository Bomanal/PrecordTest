"""Tool contracts from spec/tools.yaml.

A tool that is not in this file does not exist. INT_04 is screen-scrape only
(open item HR-306:INT_04) and has no entry.
"""

from __future__ import annotations

from typing import Any

from ..spec_loader import tools_spec

TOOL_DEFAULTS: dict[str, Any] = {
    "timeout_s": 30,
    "retry_policy": {
        "strategy": "exponential_backoff",
        "max_attempts": 3,
        "initial_delay_ms": 250,
        "max_delay_ms": 4000,
        "retry_on": ["429", "5xx", "timeout"],
    },
}


def _parse_endpoint(endpoint: str) -> tuple[str, str]:
    parts = (endpoint or "").strip().split(None, 1)
    if len(parts) == 2:
        return parts[0].upper(), parts[1]
    return "GET", endpoint or "/"


def _tools_from_spec() -> list[dict[str, Any]]:
    spec = tools_spec()
    defaults = spec.get("defaults") or TOOL_DEFAULTS
    rows: list[dict[str, Any]] = []
    for raw in spec.get("tools") or []:
        method, path = _parse_endpoint(str(raw.get("endpoint") or ""))
        direction = "write" if str(raw.get("kind", "")).lower() == "write" else "read"
        # GET surfaces are reads even when the inventory row is tagged write.
        if method == "GET":
            direction = "read"
        rows.append(
            {
                "tool_id": raw["tool_id"],
                "integration_point_id": raw.get("integration_point_id"),
                "method": method,
                "path": path,
                "direction": direction,
                "kind": raw.get("kind"),
                "auth_ref": raw.get("auth_ref"),
                "idempotency_key": raw.get("idempotency_key"),
                "timeout_s": raw.get("timeout_s") or defaults.get("timeout_s"),
                "serves_steps": raw.get("serves_steps") or [],
            }
        )
    return rows


TOOLS: list[dict[str, Any]] = _tools_from_spec()

UNAVAILABLE_TOOLS: list[dict[str, Any]] = [
    {
        "tool_id": None,
        "integration_point_id": "INT_04",
        "path": None,
        "reason": "INT_04 on case_queue_workbench needs 'screen scrape'",
        "provenance": "spec/open_items.csv@HR-306:INT_04",
        "behaviour": "No tool. Lab-report verification uses INT_06 (T-05) only.",
    }
]


def tool_by_id(tool_id: str) -> dict[str, Any]:
    for row in TOOLS:
        if row["tool_id"] == tool_id:
            return row
    raise KeyError(tool_id)


def tool_by_integration(integration_point_id: str) -> dict[str, Any]:
    for row in TOOLS:
        if row.get("integration_point_id") == integration_point_id:
            return row
    raise KeyError(integration_point_id)
