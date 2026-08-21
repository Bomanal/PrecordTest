"""Eval harness. evals/cases.csv is empty; synthetic graders cover the rubric and monitors."""

from __future__ import annotations

from typing import Any

from ..agents.base import NEVER_AUTOMATE_STEPS
from ..case_model import Case
from ..runtime import run_agent
from ..spec_loader import agent_ids, thresholds
from ..tools.catalog import TOOLS, UNAVAILABLE_TOOLS
from ..tools.mock_systems import SYNTHETIC_CASES, build_gateway


def run_evals() -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    gw = build_gateway()
    out = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-REQ-01"]),
        gateway=gw,
        stage="s3",
    )
    results.append(
        {
            "check_id": "REQS-S3-DRAFT",
            "passed": out["result"]["status"] == "checkpoint_pending"
            and bool(out["result"]["drafts"].get("email"))
            and bool(out["held_writes"]),
            "detail": "Initial APS/lab request is drafted and held for approval",
        }
    )
    results.append(
        {
            "check_id": "REQS-NO-DECISION",
            "passed": out["result"]["eval_trace"].get("never_wrote_underwriting_decision") is True,
            "detail": "Chase agent did not write underwriting_decision",
        }
    )

    gw = build_gateway()
    dup = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-REQ-02"]),
        gateway=gw,
        stage="s3",
    )
    results.append(
        {
            "check_id": "REQS-DUP-BLOCK",
            "passed": bool(dup["result"]["eval_trace"].get("duplicate_request_prevented"))
            and not dup["held_writes"],
            "detail": "Duplicate medical-record request blocked",
        }
    )

    gw = build_gateway()
    chase = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-CHASE-03"]),
        gateway=gw,
        stage="s8",
    )
    results.append(
        {
            "check_id": "REQS-S8-ESCALATE",
            "passed": chase["result"]["status"] == "escalated"
            and "chase_aging_threshold" in chase["result"]["unknowns"],
            "detail": "Aging chase escalated; threshold not invented",
        }
    )

    gw = build_gateway()
    mail = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-MAIL-04"]),
        gateway=gw,
        stage="s5",
    )
    parsed = (mail["result"]["drafts"].get("email_parse") or {})
    results.append(
        {
            "check_id": "INTAKE-EMAIL",
            "passed": parsed.get("underwriting_case_id") == "UW-MAIL-04"
            and bool(parsed.get("timeline")),
            "detail": "Email parser extracted case id and timeline",
        }
    )

    gw = build_gateway()
    bad_mail = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-MAIL-05"]),
        gateway=gw,
        stage="s5",
    )
    results.append(
        {
            "check_id": "INTAKE-LOW-CONFIDENCE",
            "passed": bad_mail["result"]["status"] == "escalated"
            and bad_mail["result"]["eval_trace"].get("status_retained") == "Awaiting records",
            "detail": "Unparsed email retained status and routed to underwriter",
        }
    )

    gw = build_gateway()
    vault = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-VAULT-06"]),
        gateway=gw,
        stage="s9",
    )
    results.append(
        {
            "check_id": "INTAKE-VAULT",
            "passed": vault["result"]["eval_trace"].get("status_advanced") == "In Review"
            and vault["result"]["eval_trace"].get("int_04_used") is False,
            "detail": "Matching lab report advanced status via INT_06, not INT_04",
        }
    )

    gw = build_gateway()
    mismatch = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-VAULT-07"]),
        gateway=gw,
        stage="s9",
    )
    results.append(
        {
            "check_id": "INTAKE-MISMATCH",
            "passed": mismatch["result"]["status"] == "escalated"
            and mismatch["result"]["eval_trace"].get("status_retained") == "Awaiting records",
            "detail": "Applicant mismatch did not auto-advance status",
        }
    )

    gw = build_gateway()
    archive = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-BOUND-08"]),
        gateway=gw,
    )
    results.append(
        {
            "check_id": "ARCHIVE-BOUND",
            "passed": bool(archive["result"]["eval_trace"].get("archived"))
            and archive["result"]["drafts"].get("archive", {}).get("underwriting_case_id")
            == "UW-BOUND-08",
            "detail": "Bound policy archived with case id, cycle_time, touches, face_amount",
        }
    )

    gw = build_gateway()
    decline = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-DECLINE-09"]),
        gateway=gw,
    )
    results.append(
        {
            "check_id": "ARCHIVE-SKIP-DECLINE",
            "passed": decline["result"]["eval_trace"].get("archived") is False
            and decline["result"]["eval_trace"].get("reason") == "alternative_outcome",
            "detail": "Decline left open for human S14",
        }
    )

    gw = build_gateway()
    failed = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-FAIL-10"]),
        gateway=gw,
    )
    results.append(
        {
            "check_id": "ARCHIVE-FAILURE",
            "passed": failed["result"]["eval_trace"].get("archived") is False
            and bool(failed["result"]["drafts"].get("it_ticket")),
            "detail": "API failure left the case open and drafted an IT ticket",
        }
    )

    results.append(
        {
            "check_id": "NEVER-AUTOMATE",
            "passed": {"S10", "S11", "S14"} <= NEVER_AUTOMATE_STEPS,
            "detail": "Clinical assessment and final decision remain human",
        }
    )
    results.append(
        {
            "check_id": "NO-INT-04",
            "passed": all(row.get("integration_point_id") != "INT_04" for row in TOOLS)
            and any(row.get("integration_point_id") == "INT_04" for row in UNAVAILABLE_TOOLS),
            "detail": "INT_04 has no tool",
        }
    )
    results.append(
        {
            "check_id": "AGENTS-LIVE",
            "passed": agent_ids() == ["BLK-REQS-CHASE", "BLK-INTAKE-MONITOR", "BLK-AUTO-ARCHIVE"],
            "detail": "Three specified agents are live",
        }
    )

    monitor = [
        {
            "metric": row.get("metric"),
            "gate_tier": row.get("gate_tier"),
            "threshold": row.get("threshold"),
            "passed": True,
            "detail": "monitor-only; empty threshold is not invented",
        }
        for row in thresholds()
        if row.get("gate_tier") == "monitor"
    ]
    passed = all(row.get("passed") for row in results)
    return {
        "passed": passed,
        "results": results,
        "monitor_thresholds": monitor,
        "precord_eval_cases": 0,
    }
