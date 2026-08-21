"""BLK-AUTO-ARCHIVE · Automated Case Archiver.

Serves S13. Autonomy: autonomous. CP-BLK-AUTO-ARCHIVE is exception-only.
Does not process Refer / Postpone / Decline (S14 stays with a person).
Does not call INT_03; that integration is not on this agent.
"""

from __future__ import annotations

from typing import Any

from ..arithmetic import cycle_time_hours
from ..case_model import Case
from ..ontology import BOUND_STATUSES, HUMAN_DECISIONS
from ..spec_loader import agent_by_id
from ..tools.catalog import tool_by_integration
from ..tools.gateway import Gateway, ToolError
from .base import AgentResult, assert_step_allowed


def run_blk_auto_archive(
    case: Case,
    gateway: Gateway,
    *,
    correlation_id: str,
    stage: str | None = None,
) -> AgentResult:
    del stage
    spec = agent_by_id("BLK-AUTO-ARCHIVE")
    result = AgentResult(
        agent_id="BLK-AUTO-ARCHIVE",
        case_id=case.case_id,
        status="completed",
        step_id="S13",
        checkpoint_id="CP-BLK-AUTO-ARCHIVE",
    )
    assert_step_allowed("S13")
    result.eval_trace["never_wrote_underwriting_decision"] = True
    result.eval_trace["int_03_used"] = False

    decision = (case.underwriting_decision or "").strip().lower()
    if decision in HUMAN_DECISIONS:
        result.eval_trace["archived"] = False
        result.eval_trace["reason"] = "alternative_outcome"
        result.notes.append(
            f"underwriting_decision is {case.underwriting_decision!r}. "
            "Refer / Postpone / Decline stay with a person (S14). Case left open."
        )
        result.shown = _shown(case, result)
        return result

    bound = _is_bound(case)
    result.eval_trace["policy_bound"] = bound
    if not bound:
        result.eval_trace["archived"] = False
        result.unknowns.append("policy_bound" if not case.status else "bound_state")
        result.notes.append(
            "Case is not in a final bound/issued state. Archive skipped; case left open."
        )
        result.shown = _shown(case, result)
        return result

    metrics = _metrics(case, result)
    archive = {
        "underwriting_case_id": case.case_id,
        "cycle_time": metrics.get("cycle_time"),
        "touches": metrics.get("touches"),
        "face_amount": metrics.get("face_amount"),
        "status": "Closed",
        "source": "BLK-AUTO-ARCHIVE",
    }
    result.drafts["archive"] = archive
    result.drafts["closed_status_note"] = (
        "INT_03 PATCH /pc/cases/{caseId}/status is not on this agent's tool list. "
        "Archive write goes to INT_07; Closed is recorded on the warehouse payload only."
    )

    try:
        warehouse = tool_by_integration("INT_07")
        key = gateway.idempotency_key(
            warehouse["idempotency_key"],
            correlation_id=correlation_id,
            payload=archive,
        )
        # tools.yaml lists GET; the prompt requires an archive write on INT_07.
        call = gateway.call(
            warehouse["tool_id"],
            "POST",
            "/warehouse/v1/underwriting/cases",
            direction="write",
            payload=archive,
            idempotency_key=key,
            hold_write=False,
            correlation_id=correlation_id,
        )
        result.writes.append(
            {"tool": warehouse["tool_id"], "payload": archive, "status": call.status}
        )
        result.eval_trace["archived"] = True
        result.notes.append("Bound policy archived. Case marked Closed on the historical repository.")
    except ToolError as exc:
        result.status = "error"
        result.eval_trace["archived"] = False
        result.escalation_queue = spec["failure_behaviour"]
        result.notes.append(
            f"Archive failed; case left open. {exc}"
        )
        _it_ticket(case, result, str(exc))
        result.status = "checkpoint_pending"
        result.notes.append("Exception routed to CP-BLK-AUTO-ARCHIVE / IT Operations.")

    result.shown = _shown(case, result)
    return result


def _is_bound(case: Case) -> bool:
    if case.policy_bound and case.policy_issued:
        return True
    status = (case.status or "").strip().lower()
    return status in BOUND_STATUSES


def _metrics(case: Case, result: AgentResult) -> dict[str, Any]:
    hours = cycle_time_hours(case.application_received_at, case.bound_at)
    cycle = case.cycle_time
    if hours is not None:
        cycle = f"{hours} hours"
    elif not cycle:
        result.unknowns.append("cycle_time")
    if case.touches is None:
        result.unknowns.append("touches")
    if case.face_amount is None:
        result.unknowns.append("face_amount")
    return {
        "underwriting_case_id": case.case_id,
        "cycle_time": cycle,
        "cycle_time_hours": hours,
        "touches": case.touches,
        "face_amount": case.face_amount,
    }


def _it_ticket(case: Case, result: AgentResult, detail: str) -> None:
    payload = {
        "queue": "IT Operations support desk",
        "underwriting_case_id": case.case_id,
        "detail": detail,
        "leave_case_open": True,
    }
    result.drafts["it_ticket"] = payload
    result.notes.append(
        "No ITSM tool is declared in spec/tools.yaml. Ticket payload retained as a draft "
        "for the IT Operations support desk queue."
    )


def _shown(case: Case, result: AgentResult) -> dict[str, Any]:
    return {
        "underwriting_case_id": case.case_id,
        "status": case.status,
        "underwriting_decision": case.underwriting_decision,
        "archive": result.drafts.get("archive"),
        "it_ticket": result.drafts.get("it_ticket"),
        "notes": result.notes,
    }
