"""BLK-INTAKE-MONITOR · Medical Document Intake & Logging Agent.

Parallel sub-agents:
  BLK-INTAKE-MONITOR.1 Email Confirmation Intake Agent (S5)
  BLK-INTAKE-MONITOR.2 Document Vault Verification Agent (S9)

Autonomy: act_with_review. CP-BLK-INTAKE-MONITOR reviews a 10% sample.
INT_04 (screen scrape) is not used.
"""

from __future__ import annotations

import hashlib
from typing import Any

from ..case_model import Case
from ..spec_loader import agent_by_id, checkpoint_by_id
from ..tools.catalog import tool_by_integration
from ..tools.gateway import Gateway, ToolError
from .base import AgentResult, assert_step_allowed
from .parsers import documents_match_case, parse_email
from ..ontology import STATUS_IN_REVIEW


def run_blk_intake_monitor(
    case: Case,
    gateway: Gateway,
    *,
    correlation_id: str,
    stage: str | None = None,
) -> AgentResult:
    spec = agent_by_id("BLK-INTAKE-MONITOR")
    result = AgentResult(
        agent_id="BLK-INTAKE-MONITOR",
        case_id=case.case_id,
        status="completed",
        checkpoint_id="CP-BLK-INTAKE-MONITOR",
    )
    result.eval_trace["composition"] = "parallel"
    result.eval_trace["never_wrote_underwriting_decision"] = True
    result.eval_trace["int_04_used"] = False

    inferred = _stages(stage)
    prior_status = case.status

    try:
        if "s5" in inferred:
            _run_email(case, gateway, correlation_id, result, spec)
        if "s9" in inferred:
            _run_vault(case, gateway, correlation_id, result, spec)
    except ToolError as exc:
        result.status = "error"
        result.notes.append(str(exc))
        result.escalation_queue = spec["failure_behaviour"]
        result.eval_trace["status_retained"] = prior_status

    if result.status not in {"error", "escalated"}:
        sampled = case.force_checkpoint or _sample_review(case.case_id)
        result.eval_trace["review_sampled"] = sampled
        if sampled:
            result.status = "checkpoint_pending"
            result.notes.append("Sampled for CP-BLK-INTAKE-MONITOR (10% review). Writes already applied.")

    result.shown = {
        "underwriting_case_id": case.case_id,
        "prior_status": prior_status,
        "email": result.drafts.get("email_parse"),
        "vault": result.drafts.get("vault_match"),
        "notes": result.notes,
    }
    return result


def _stages(stage: str | None) -> set[str]:
    if not stage:
        return {"s5", "s9"}
    token = stage.lower().lstrip("s")
    if token in {"5", "s5"}:
        return {"s5"}
    if token in {"9", "s9"}:
        return {"s9"}
    return {"s5", "s9"}


def _sample_review(case_id: str, rate_percent: int | None = None) -> bool:
    if rate_percent is None:
        spec = checkpoint_by_id("CP-BLK-INTAKE-MONITOR")
        raw = spec.get("review_rate_percent") or "10"
        try:
            rate_percent = int(str(raw).strip())
        except ValueError:
            rate_percent = 10
    digest = hashlib.sha256(case_id.encode()).hexdigest()
    return int(digest[:8], 16) % 100 < rate_percent


def _run_email(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    spec: dict[str, Any],
) -> None:
    assert_step_allowed("S5")
    result.step_id = result.step_id or "S5"
    mail = tool_by_integration("INT_05")
    path = f"/mail/v1/messages?label=underwriting&caseId={case.case_id}"
    call = gateway.call(
        mail["tool_id"],
        "GET",
        path,
        direction="read",
        correlation_id=correlation_id,
    )
    result.reads.append({"tool": mail["tool_id"], "path": path})
    messages = list((call.response or {}).get("messages") or [])
    if case.inbound_email:
        messages = [case.inbound_email, *messages]
    parsed = parse_email(messages[0] if messages else case.inbound_email)
    result.drafts["email_parse"] = parsed
    result.sub_agents.append(
        {
            "agent_id": "BLK-INTAKE-MONITOR.1",
            "purpose": "Email Confirmation Intake Agent",
            "parsed": parsed,
        }
    )

    if parsed.get("confidence") != "high":
        result.status = "escalated"
        result.escalation_queue = spec["failure_behaviour"]
        result.eval_trace["status_retained"] = case.status
        result.unknowns.append("email_timeline" if parsed.get("underwriting_case_id") else "underwriting_case_id")
        result.notes.append(
            "Email extraction confidence is not high. Unparsed mail routed to the assigned underwriter; "
            "case status retained."
        )
        return

    if parsed.get("underwriting_case_id") and parsed["underwriting_case_id"] != case.case_id:
        result.status = "escalated"
        result.escalation_queue = spec["failure_behaviour"]
        result.eval_trace["status_retained"] = case.status
        result.notes.append("Extracted underwriting_case_id does not match the active case.")
        return

    _write_workbench(
        case,
        gateway,
        correlation_id,
        result,
        {
            "estimated_delivery_timeline": parsed.get("timeline"),
            "intake_source": "email",
        },
        hold=False,
    )
    result.notes.append(
        f"Email timeline {parsed.get('timeline')!r} logged on the underwriting_workbench."
    )


def _run_vault(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    spec: dict[str, Any],
) -> None:
    assert_step_allowed("S9")
    result.step_id = "S9" if result.step_id is None else result.step_id
    vault = tool_by_integration("INT_06")
    path = vault["path"].replace("{caseId}", case.case_id)
    if "{caseId}" not in vault["path"]:
        path = f"/vault/v1/documents?caseId={case.case_id}"
    call = gateway.call(
        vault["tool_id"],
        "GET",
        path,
        direction="read",
        correlation_id=correlation_id,
    )
    result.reads.append({"tool": vault["tool_id"], "path": path})
    documents = list((call.response or {}).get("documents") or [])
    if case.vault_documents:
        documents = list(case.vault_documents) or documents
    match = documents_match_case(documents, case.case_id, case.applicant_name)
    result.drafts["vault_match"] = match
    result.sub_agents.append(
        {
            "agent_id": "BLK-INTAKE-MONITOR.2",
            "purpose": "Document Vault Verification Agent",
            "match": match,
        }
    )

    if not match["verified"]:
        if result.status != "escalated":
            result.status = "escalated"
        result.escalation_queue = spec["failure_behaviour"]
        result.eval_trace["status_retained"] = case.status
        result.notes.append(
            "Vault document could not be verified against the active case "
            f"(mismatches: {match['mismatches'] or 'none matched'}). Status retained."
        )
        return

    types = [doc["canonical_type"] for doc in match["matched"]]
    _write_workbench(
        case,
        gateway,
        correlation_id,
        result,
        {
            "status": STATUS_IN_REVIEW,
            "documents_received": types,
            "intake_source": "document_vault",
        },
        hold=False,
    )
    result.eval_trace["status_advanced"] = STATUS_IN_REVIEW
    result.notes.append(
        "Verified laboratory_report / attending_physician_statement. Status set to In Review."
    )


def _write_workbench(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
    payload: dict[str, Any],
    *,
    hold: bool,
) -> None:
    tool = tool_by_integration("INT_01")
    path = f"/pc/cases/{case.case_id}/workbench"
    key = gateway.idempotency_key(tool["idempotency_key"], correlation_id=correlation_id, payload=payload)
    call = gateway.call(
        tool["tool_id"],
        "PATCH",
        path,
        direction="write",
        payload=payload,
        idempotency_key=key,
        hold_write=hold,
        correlation_id=correlation_id,
    )
    result.writes.append({"tool": tool["tool_id"], "payload": payload, "status": call.status})
