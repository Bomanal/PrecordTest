"""Tool contracts implemented by this workbench.

The Precord package's spec/tools.yaml is empty (HR-201). This file is the
implementation inventory: every write is idempotent; reads and writes stay apart.
"""

from __future__ import annotations

from typing import Any

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

TOOLS: list[dict[str, Any]] = [
    {
        "tool_id": "medical_grid_lookup",
        "method": "GET",
        "path": "/underwriting/medical-grid",
        "direction": "read",
        "system": "SYS_01",
        "serves": ["BLK-01.1"],
        "idempotency_key": None,
        "provenance": "integration_point_inventory@row:IP_01",
    },
    {
        "tool_id": "order_medical_tests",
        "method": "POST",
        "path": "/submissions/{id}/medical/tests",
        "direction": "write",
        "system": "SYS_01",
        "serves": ["BLK-01.1"],
        "idempotency_key": "BLK-01:{case_id}:order_medical_tests:{payload_hash}",
        "held_until_checkpoint": True,
        "provenance": "integration_point_inventory@row:IP_02",
    },
    {
        "tool_id": "read_document",
        "method": "GET",
        "path": "/documents/{docId}",
        "direction": "read",
        "system": "SYS_01",
        "serves": ["BLK-01.3"],
        "idempotency_key": None,
        "provenance": "integration_point_inventory@row:IP_03",
    },
    {
        "tool_id": "record_medical_results",
        "method": "POST",
        "path": "/submissions/{id}/medical/results",
        "direction": "write",
        "system": "SYS_01",
        "serves": ["BLK-01.3"],
        "idempotency_key": "BLK-01:{case_id}:record_medical_results:{payload_hash}",
        "held_until_checkpoint": True,
        "provenance": "integration_point_inventory@row:IP_04",
    },
    {
        "tool_id": "rating_override",
        "method": "POST",
        "path": "/submissions/{id}/rating/override",
        "direction": "write",
        "system": "SYS_01",
        "serves": ["BLK-02.1"],
        "idempotency_key": "BLK-02:{case_id}:rating_override:{payload_hash}",
        "held_until_checkpoint": True,
        "provenance": "integration_point_inventory@row:IP_06",
    },
    {
        "tool_id": "treaty_limits_lookup",
        "method": "GET",
        "path": "/reinsurance/treaty-limits",
        "direction": "read",
        "system": "SYS_01",
        "serves": ["BLK-02.2"],
        "idempotency_key": None,
        "provenance": "technical_transformation_specification@Q3",
        "note": "Retention Limit value itself is OI-01. The tool is called; a blank response is a halt.",
    },
    {
        "tool_id": "dispatch_facultative_referral",
        "method": "POST",
        "path": "/reinsurance/referrals",
        "direction": "write",
        "system": "SYS_01",
        "serves": ["BLK-02.2"],
        "idempotency_key": "BLK-02:{case_id}:dispatch_facultative_referral:{payload_hash}",
        "held_until_checkpoint": True,
        "provenance": "technical_transformation_specification@Q3",
    },
    {
        "tool_id": "create_manual_task",
        "method": "POST",
        "path": "/submissions/{id}/tasks",
        "direction": "write",
        "system": "SYS_01",
        "serves": ["BLK-01", "BLK-02"],
        "idempotency_key": "{agent_id}:{case_id}:create_manual_task:{payload_hash}",
        "provenance": "agent_specifications@failure_behaviour",
    },
]

# IP_05 is not available. Provisional Atlas Re dispatch has no write tool.
UNAVAILABLE_TOOLS: list[dict[str, Any]] = [
    {
        "tool_id": "dispatch_provisional_referral",
        "path": None,
        "reason": "IP_05 on SYS_02 needs 'not available'",
        "provenance": "integration_point_inventory@row:IP_05;spec/open_items.csv@HR-306:INT_01",
        "behaviour": "Store a draft on the case. Do not dispatch.",
    }
]
