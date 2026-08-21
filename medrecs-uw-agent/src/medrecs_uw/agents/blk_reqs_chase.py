"""BLK-REQS-CHASE · Underwriting Requirements and Chase Orchestrator.

Serves S3 (initial medical-record request) and S8 (aging follow-up).
Autonomy: draft_for_approval. Checkpoint CP-BLK-REQS-CHASE is always on.
"""

from __future__ import annotations

from typing import Any

from ..case_model import Case
from ..observability import DUPLICATE_BLOCKS, MANUAL_CHASES
from ..ontology import (
    ATTENDING_PHYSICIAN_STATEMENT,
    LABORATORY_REPORT,
    STATUS_MANUAL_RECORD_REQUEST_REQUIRED,
)
from ..spec_loader import agent_by_id
from ..tools.catalog import tool_by_integration
from ..tools.gateway import Gateway, ToolError
from .base import AgentResult, assert_step_allowed


def run_blk_reqs_chase(
    case: Case,
    gateway: Gateway,
    *,
    correlation_id: str,
    stage: str | None = None,
) -> AgentResult:
    spec = agent_by_id("BLK-REQS-CHASE")
    result = AgentResult(
        agent_id="BLK-REQS-CHASE",
        case_id=case.case_id,
        status="checkpoint_pending",
        checkpoint_id="CP-BLK-REQS-CHASE",
    )
    result.eval_trace["never_wrote_underwriting_decision"] = True
    result.eval_trace["clinical_assessment"] = False

    if not case.underwriting_case_id and not case.case:
        result.status = "escalated"
        result.unknowns.append("underwriting_case_id")
        result.escalation_queue = spec["failure_behaviour"]
        result.notes.append("underwriting_case_id is unknown. Escalate rather than infer.")
        result.shown = _shown(case, result)
        return result

    workbench = _read_workbench(gateway, correlation_id, result)
    merged = _merge_case(case, workbench)

    inferred = (stage or _infer_stage(merged)).lower().lstrip("s")
    inferred = f"s{inferred}" if inferred in {"3", "8"} else inferred

    try:
        if inferred == "s8":
            _run_s8(merged, gateway, correlation_id, result, spec)
        else:
            _run_s3(merged, gateway, correlation_id, result, spec)
    except ToolError as exc:
        _fail_to_underwriter(merged, gateway, correlation_id, result, spec, str(exc))

    result.shown = _shown(merged, result)
    return result


def _infer_stage(case: Case) -> str:
    aging = (case.aging or "").strip()
    pending = "pending" in (case.status or "").lower() or "awaiting" in (case.status or "").lower()
    if aging and aging not in {"0 days", "0"} and pending:
        return "s8"
    if aging and "day" in aging.lower() and not aging.startswith("0"):
        received = case.received_types()
        needed = _needed(case, received)
        if needed:
            return "s8"
    return "s3"


def _needed(case: Case, received: set[str]) -> list[str]:
    needed: list[str] = []
    if case.attending_physician_statement_required and ATTENDING_PHYSICIAN_STATEMENT not in received:
        needed.append(ATTENDING_PHYSICIAN_STATEMENT)
    if case.laboratory_report_required and LABORATORY_REPORT not in received:
        needed.append(LABORATORY_REPORT)
    if not needed and not case.attending_physician_statement_required and not case.laboratory_report_required:
        # Schema/surface gap: requirement flags unknown. Escalate rather than invent.
        return []
    return needed


def _run_s3(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    spec: dict[str, Any],
) -> None:
    assert_step_allowed("S3")
    result.step_id = "S3"
    received = case.received_types()
    needed = _needed(case, received)
    result.eval_trace["documents_already_received"] = sorted(received)
    result.eval_trace["requirements_needed"] = needed

    if not case.attending_physician_statement_required and not case.laboratory_report_required:
        result.status = "escalated"
        result.unknowns.append("attending_physician_statement_required")
        result.notes.append(
            "Whether an attending_physician_statement or laboratory_report is required is unknown. "
            "Escalate rather than inventing a requirement."
        )
        result.escalation_queue = spec["failure_behaviour"]
        return

    if not needed:
        DUPLICATE_BLOCKS.inc()
        result.eval_trace["duplicate_request_prevented"] = True
        result.drafts["request"] = None
        result.status = "completed"
        result.notes.append(
            "Documents already verified as received. Duplicate medical-record request not sent."
        )
        return

    draft = {
        "to": "agent_or_clinic",
        "assigned_underwriter": case.assigned_underwriter,
        "underwriting_case_id": case.case_id,
        "subject": f"Medical records request — {case.case_id}",
        "body": (
            f"Please send the following for underwriting_case_id {case.case_id}: "
            + ", ".join(needed)
            + ". Do not reply with clinical interpretation."
        ),
        "requirements": needed,
        "template": "initial_records_request",
        "send": False,
    }
    result.drafts["email"] = draft
    mail = tool_by_integration("INT_05")
    key = gateway.idempotency_key(
        mail["idempotency_key"],
        correlation_id=correlation_id,
        payload=draft,
    )
    call = gateway.call(
        mail["tool_id"],
        "POST",
        "/mail/v1/messages",
        direction="write",
        payload=draft,
        idempotency_key=key,
        hold_write=True,
        correlation_id=correlation_id,
    )
    result.writes.append(
        {"tool": mail["tool_id"], "held": True, "payload": draft, "status": call.status}
    )
    result.notes.append(
        "Initial request drafted and held for CP-BLK-REQS-CHASE. "
        "Guardrail: drafted emails require underwriter approval before send."
    )
    result.status = "checkpoint_pending"


def _run_s8(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    spec: dict[str, Any],
) -> None:
    assert_step_allowed("S8")
    result.step_id = "S8"
    MANUAL_CHASES.inc()
    result.eval_trace["aging"] = case.aging
    result.eval_trace["chase_threshold"] = "unknown"
    result.eval_trace["duplicate_request_prevented"] = True
    result.unknowns.append("chase_aging_threshold")
    result.status = "escalated"
    result.escalation_queue = spec["failure_behaviour"]
    result.notes.append(
        f"Case aging is {case.aging!r}. Exact aging thresholds for chasing are unknown. "
        "Escalate to the assigned underwriter instead of inventing a chase rule. "
        "S7 (whether a case warrants a manual chase) stays with a person."
    )
    _tag_manual_request(case, gateway, correlation_id, result)


def _read_workbench(gateway: Gateway, correlation_id: str, result: AgentResult) -> dict[str, Any] | None:
    tool = tool_by_integration("INT_01")
    try:
        call = gateway.call(
            tool["tool_id"],
            tool["method"],
            tool["path"] if "?" in tool["path"] else f"{tool['path']}?status=open",
            direction="read",
            correlation_id=correlation_id,
        )
    except ToolError:
        raise
    result.reads.append({"tool": tool["tool_id"], "path": tool["path"]})
    cases = (call.response or {}).get("cases") or []
    for row in cases:
        if row.get("underwriting_case_id") == result.case_id or row.get("case") == result.case_id:
            return row
    return None


def _merge_case(case: Case, workbench: dict[str, Any] | None) -> Case:
    if not workbench:
        return case
    data = case.model_dump()
    for key, value in workbench.items():
        if data.get(key) in (None, "", [], False) and value not in (None, "", []):
            data[key] = value
    return Case.model_validate(data)


def _fail_to_underwriter(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    spec: dict[str, Any],
    message: str,
) -> None:
    result.status = "error"
    result.notes.append(message)
    result.escalation_queue = spec["failure_behaviour"]
    _tag_manual_request(case, gateway, correlation_id, result)


def _tag_manual_request(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
) -> None:
    tool = tool_by_integration("INT_01")
    payload = {
        "status": STATUS_MANUAL_RECORD_REQUEST_REQUIRED,
        "failure_note": "; ".join(result.notes) or "Manual record request required",
        "assigned_underwriter": case.assigned_underwriter,
    }
    path = f"/pc/cases/{case.case_id}/workbench"
    key = gateway.idempotency_key(tool["idempotency_key"], correlation_id=correlation_id, payload=payload)
    try:
        call = gateway.call(
            tool["tool_id"],
            "PATCH",
            path,
            direction="write",
            payload=payload,
            idempotency_key=key,
            hold_write=result.status == "checkpoint_pending",
            correlation_id=correlation_id,
        )
        result.writes.append({"tool": tool["tool_id"], "payload": payload, "status": call.status})
    except ToolError as exc:
        result.notes.append(f"Failed to tag Case Queue Workbench: {exc}")


def _shown(case: Case, result: AgentResult) -> dict[str, Any]:
    return {
        "underwriting_case_id": case.case_id,
        "status": case.status,
        "aging": case.aging,
        "assigned_underwriter": case.assigned_underwriter,
        "requirements_needed": result.eval_trace.get("requirements_needed"),
        "email_draft": result.drafts.get("email"),
        "notes": result.notes,
    }
