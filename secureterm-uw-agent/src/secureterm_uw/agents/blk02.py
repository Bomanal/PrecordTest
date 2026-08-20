"""BLK-02 Rating Compliance & Referral Dispatch.

Sequential sub-agents:
  BLK-02.1 Rating Compliance Auditor (S8)
  BLK-02.2 Reinsurance Referral Dispatcher (S9)

Final decision (S11) and policy issue (S15) are never written.
"""

from __future__ import annotations

from typing import Any

from ..arithmetic import override_reason_is_valid, parse_em_percent
from ..case_model import Case
from ..ontology import ATLAS_RE, HAZARDOUS_OCCUPATION
from ..open_items import halt
from ..spec_loader import agent_by_id
from ..tools.catalog import TOOLS
from ..tools.gateway import Gateway, ToolError
from .base import AgentResult, assert_step_allowed

EM_REFERRAL_THRESHOLD = 150.0  # stated in process_step_table@S9 and prompts/BLK-02.md
HAZARDOUS_CUES = {"hazardous", "aviation crew", "merchant navy", "uninsurable"}


def _tool(tool_id: str) -> dict[str, Any]:
    for row in TOOLS:
        if row["tool_id"] == tool_id:
            return row
    raise KeyError(tool_id)


def _is_hazardous(case: Case) -> bool:
    blob = f"{case.occupation or ''} {case.occupation_class or ''}".lower()
    return any(cue in blob for cue in HAZARDOUS_CUES)


def run_blk02(
    case: Case,
    gateway: Gateway,
    *,
    correlation_id: str,
) -> AgentResult:
    spec = agent_by_id("BLK-02")
    case_id = case.case_identifier or "unknown"
    result = AgentResult(
        agent_id="BLK-02",
        case_id=case_id,
        status="checkpoint_pending",
        checkpoint_id=spec["checkpoints"][0],
        step_id="S8",
    )

    if case.sum_insured_conflict():
        stop = halt("OI-04", "Sum Assured for Facultative Referral trigger")
        result.status = "open_item"
        result.open_items.append(stop.item_id)
        result.unknowns.append("sum_assured")
        result.notes.append(stop.message)
        result.escalation_queue = "Chief Underwriting Officer review queue"
        return result

    _audit_override(case, gateway, correlation_id, result)
    if result.status in {"blocked", "error"}:
        result.shown = _shown(case)
        return result

    _referral(case, gateway, correlation_id, result)
    result.shown = _shown(case)
    return result


def _audit_override(
    case: Case, gateway: Gateway, correlation_id: str, result: AgentResult
) -> None:
    assert_step_allowed("S8")
    override = case.underwriter_override
    reason = case.override_reason_mandatory_field_completed
    suggested = case.rating_engine_suggested_em
    result.eval_trace["val_03_01"] = "not_applicable"
    result.drafts["rating_engine_suggested_em"] = suggested
    result.drafts["underwriter_override"] = override

    if override in (None, "", suggested):
        result.notes.append("No Extra Mortality override to submit.")
        return

    valid = override_reason_is_valid(reason)
    result.eval_trace["val_03_01"] = "pass" if valid else "fail"
    if not valid:
        result.status = "blocked"
        result.escalation_queue = "Chief Underwriting Officer review queue"
        result.notes.append(
            "VAL-03-01: Override reason is mandatory when underwriter override Extra Mortality "
            "is modified. API submission blocked."
        )
        result.drafts["override_flag"] = {
            "field": "override_reason_mandatory_field_completed",
            "surface": "SURF-03 Pricing & Risk",
            "enforcement": "blocking",
        }
        return

    tool = _tool("rating_override")
    path = tool["path"].replace("{id}", result.case_id)
    payload = {
        "underwriter_override": override,
        "override_reason": reason,
        "rating_engine_suggested_em": suggested,
    }
    key = gateway.idempotency_key(
        tool["idempotency_key"], case_id=result.case_id, payload=payload
    )
    call = gateway.call(
        tool["tool_id"],
        tool["method"],
        path,
        direction="write",
        payload=payload,
        idempotency_key=key,
        hold_write=True,
        correlation_id=correlation_id,
    )
    result.writes.append(
        {"tool": tool["tool_id"], "held": True, "payload": payload, "status": call.status}
    )
    result.notes.append("Override payload held for CP-BLK-02 approval.")


def _referral(
    case: Case,
    gateway: Gateway,
    correlation_id: str,
    result: AgentResult,
) -> None:
    assert_step_allowed("S9")
    tool = _tool("treaty_limits_lookup")
    try:
        call = gateway.call(
            tool["tool_id"],
            tool["method"],
            tool["path"],
            direction="read",
            correlation_id=correlation_id,
        )
    except ToolError as exc:
        result.status = "error"
        result.notes.append(str(exc))
        result.escalation_queue = "Chief Underwriting Officer review queue"
        return

    result.reads.append({"tool": tool["tool_id"], "response": call.response})
    treaty = call.response or {}
    result.drafts["treaty_limits"] = treaty

    retention = treaty.get("retention_limit")
    if retention is None or treaty.get("open_item") == "OI-01":
        stop = halt("OI-01", "comparing Sum Assured to Retention Limit")
        result.open_items.append(stop.item_id)
        result.notes.append(stop.message)
        # Still evaluate stated S9 triggers that do not depend on retention.
        retention_exceeded = None
    else:
        retention_exceeded = (case.sum_assured or 0) > float(retention)

    em = parse_em_percent(case.underwriter_override) or parse_em_percent(
        case.rating_engine_suggested_em
    )
    em_trigger = em is not None and em > EM_REFERRAL_THRESHOLD
    hazardous = _is_hazardous(case)
    triggers = {
        "retention_limit_exceeded": retention_exceeded,
        "extra_mortality_gt_150": em_trigger,
        "hazardous_occupation": hazardous,
    }
    result.drafts["referral_triggers"] = triggers
    result.eval_trace["referral_triggers"] = triggers

    should_refer = any(value is True for value in triggers.values())
    if retention_exceeded is None and not should_refer:
        result.unknowns.append("retention_limit")
        result.escalation_queue = "Chief Underwriting Officer review queue"
        result.notes.append(
            "Cannot decide Facultative Referral on Sum Assured vs Retention Limit (OI-01). "
            "No other S9 trigger fired. Halt rather than invent a limit."
        )
        if result.status != "blocked":
            result.status = "checkpoint_pending" if result.writes else "open_item"
        return

    if not should_refer:
        result.notes.append("No Facultative Referral trigger met.")
        if result.status != "blocked":
            result.status = "checkpoint_pending"
        return

    package = {
        "referred_to": ATLAS_RE if (hazardous or em_trigger or retention_exceeded) else "Chief Underwriting Officer",
        "case_identifier": case.case_identifier,
        "proposer_life_assured": case.proposer_life_assured,
        "product": case.product,
        "term": case.term,
        "sum_assured": case.sum_assured,
        "occupation": case.occupation,
        "extra_mortality": em,
        "override_reason": case.override_reason_mandatory_field_completed,
        "triggers": {k: v for k, v in triggers.items() if v},
        "kind": "facultative",
    }
    if HAZARDOUS_OCCUPATION.lower() in f"{case.occupation} {case.occupation_class}".lower() or hazardous:
        package["hazard"] = HAZARDOUS_OCCUPATION
    result.drafts["facultative_referral"] = package

    write = _tool("dispatch_facultative_referral")
    key = gateway.idempotency_key(
        write["idempotency_key"], case_id=result.case_id, payload=package
    )
    call = gateway.call(
        write["tool_id"],
        write["method"],
        write["path"],
        direction="write",
        payload=package,
        idempotency_key=key,
        hold_write=True,
        correlation_id=correlation_id,
    )
    result.writes.append(
        {"tool": write["tool_id"], "held": True, "payload": package, "status": call.status}
    )
    result.notes.append(
        "Facultative Referral package drafted and held for CP-BLK-02. "
        "Final underwriting decision is not recorded."
    )
    if result.status != "blocked":
        result.status = "checkpoint_pending"
        result.step_id = "S9"


def _shown(case: Case) -> dict[str, Any]:
    return {
        "case_identifier": case.case_identifier,
        "proposer_life_assured": case.proposer_life_assured,
        "product": case.product,
        "term": case.term,
        "sum_assured": case.sum_assured,
        "decision_status_header": case.decision_status_header,
        "rating_engine_suggested_em": case.rating_engine_suggested_em,
        "underwriter_override": case.underwriter_override,
        "referred_to": case.referred_to,
        "reinsurer_terms": case.reinsurer_terms,
        "decision": case.decision,
        "override_reason_mandatory_field_completed": case.override_reason_mandatory_field_completed,
    }
