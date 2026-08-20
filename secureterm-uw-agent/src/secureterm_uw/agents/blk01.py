"""BLK-01 Medical Processing & Referral Orchestration.

Sequential sub-agents:
  BLK-01.1 Medical Requirements Evaluator (S3)
  BLK-01.2 Early Referral Formatter (S4)
  BLK-01.3 Clinical Evidence Ingestion & Validator (S6)

S2, S11, S15 are never touched.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..arithmetic import UnitParseError, calculate_bmi
from ..case_model import Case
from ..ontology import ATLAS_RE, HAZARDOUS_OCCUPATION
from ..open_items import halt
from ..spec_loader import agent_by_id
from ..tools.catalog import TOOLS
from ..tools.gateway import Gateway, ToolError
from .base import AgentResult, assert_step_allowed
from .mer_parser import parse_mer_text

HAZARDOUS_CUES = {"hazardous", "aviation crew", "merchant navy", "uninsurable"}
PROVISIONAL_SUM_TRIGGER_INR = 25_000_000  # opportunity_table@OPP-03; not OI-01 retention


def _tool(tool_id: str) -> dict[str, Any]:
    for row in TOOLS:
        if row["tool_id"] == tool_id:
            return row
    raise KeyError(tool_id)


def _is_hazardous(case: Case) -> bool:
    blob = f"{case.occupation or ''} {case.occupation_class or ''}".lower()
    return any(cue in blob for cue in HAZARDOUS_CUES)


def _smoker_unverified(case: Case) -> bool:
    status = (case.smoker_status or case.tobacco_use or "").strip().lower()
    return status in {"", "unknown", "unverified"}


def run_blk01(
    case: Case,
    gateway: Gateway,
    *,
    correlation_id: str,
    stage: str | None = None,
) -> AgentResult:
    """stage: s3 | s4 | s6 | None (auto from available evidence)."""
    spec = agent_by_id("BLK-01")
    case_id = case.case_identifier or "unknown"
    result = AgentResult(
        agent_id="BLK-01",
        case_id=case_id,
        status="checkpoint_pending",
        checkpoint_id="CP-BLK-01",
    )

    if case.sum_insured_conflict():
        stop = halt("OI-04", "Sum Assured for medical-grid lookup")
        result.status = "open_item"
        result.open_items.append(stop.item_id)
        result.unknowns.append("sum_assured")
        result.escalation_queue = spec["failure_behaviour"]
        result.notes.append(stop.message)
        _manual_task(gateway, case_id, stop.message, correlation_id, result)
        return result

    if _smoker_unverified(case) or case.age_last_birthday is None:
        result.status = "escalated"
        result.escalation_queue = "Intake & Underwriting Assessment manual queue"
        result.unknowns.append("smoker_status" if _smoker_unverified(case) else "age_last_birthday")
        result.notes.append(
            "Escalate: applicant smoker status is unverified or demographic values are corrupt."
        )
        return result

    inferred_stage = stage or _infer_stage(case)
    if inferred_stage == "s3":
        _run_s3(case, gateway, correlation_id, result)
    elif inferred_stage == "s4":
        _run_s3(case, gateway, correlation_id, result)
        if result.status not in {"escalated", "open_item", "error"}:
            _run_s4(case, gateway, correlation_id, result)
    elif inferred_stage == "s6":
        _run_s6(case, gateway, correlation_id, result)
    else:
        result.unknowns.append("stage")
        result.notes.append("Could not determine whether this invocation is S3, S4 or S6.")
        result.status = "escalated"
        result.escalation_queue = "Intake & Underwriting Assessment manual queue"

    result.shown = _checkpoint_shown(case, result)
    return result


def _infer_stage(case: Case) -> str:
    if case.mer_text or case.mer_reference or case.height or case.weight:
        return "s6"
    if _is_hazardous(case) or (case.sum_assured or 0) > PROVISIONAL_SUM_TRIGGER_INR:
        return "s4"
    return "s3"


def _run_s3(case: Case, gateway: Gateway, correlation_id: str, result: AgentResult) -> None:
    assert_step_allowed("S3")
    result.step_id = "S3"
    cues = case.preliminary_cues()
    result.eval_trace["fast_track_cues_used"] = [
        "Sum Assured",
        "Non-Medical Limit",
        "occupation",
        "age",
        "smoker status",
    ]
    result.eval_trace["opened_clinical_or_financial"] = False
    result.eval_trace["clinical_fields_read"] = []
    missing = [k for k, v in cues.items() if v in (None, "")]
    if missing:
        result.unknowns.extend(missing)
        result.status = "escalated"
        result.escalation_queue = "Intake & Underwriting Assessment manual queue"
        result.notes.append(f"Preliminary cues unknown: {missing}")
        return

    grid_tool = _tool("medical_grid_lookup")
    query = urlencode(
        {"age": case.age_last_birthday, "sumInsured": int(case.sum_assured or 0)}
    )
    path = f"{grid_tool['path']}?{query}"
    try:
        call = gateway.call(
            grid_tool["tool_id"],
            grid_tool["method"],
            path,
            direction="read",
            correlation_id=correlation_id,
        )
    except ToolError as exc:
        result.status = "error"
        result.notes.append(str(exc))
        _manual_task(gateway, result.case_id, str(exc), correlation_id, result)
        return

    result.reads.append({"tool": grid_tool["tool_id"], "response": call.response})
    grid = call.response or {}
    result.eval_trace["nml_band"] = grid.get("nml_band")
    result.drafts["medical_grid"] = grid
    if grid.get("open_item") == "OI-02":
        result.notes.append(
            "Medical grid values came from a synthetic fixture because OI-02 is open. "
            "Do not treat nml_band as client Non-Medical Limit."
        )

    nml_eligible = bool(grid.get("nml_eligible"))
    hazardous = _is_hazardous(case)
    early = hazardous or (case.sum_assured or 0) > PROVISIONAL_SUM_TRIGGER_INR
    if early:
        result.eval_trace["s3_route"] = "early_reinsurer_referral"
        result.drafts["fast_track"] = False
        result.notes.append(
            "Case flagged for early Facultative Referral path using preliminary cues only."
        )
        return
    if nml_eligible and not hazardous:
        result.eval_trace["s3_route"] = "non_medical_fast_track"
        result.drafts["fast_track"] = True
        result.notes.append(
            "Fast-track: Non-Medical Limit eligible on preliminary cues. "
            "Health declaration (S7) stays with a person."
        )
        return

    tests = list(grid.get("required_tests") or [])
    result.eval_trace["s3_route"] = "order_medicals"
    result.drafts["fast_track"] = False
    result.drafts["tests_to_order"] = tests
    order_tool = _tool("order_medical_tests")
    path = order_tool["path"].replace("{id}", result.case_id)
    payload = {"tests": tests, "source": "medical-grid"}
    key = gateway.idempotency_key(
        order_tool["idempotency_key"],
        case_id=result.case_id,
        payload=payload,
    )
    call = gateway.call(
        order_tool["tool_id"],
        order_tool["method"],
        path,
        direction="write",
        payload=payload,
        idempotency_key=key,
        hold_write=True,
        correlation_id=correlation_id,
    )
    result.writes.append(
        {"tool": order_tool["tool_id"], "held": True, "payload": payload, "status": call.status}
    )
    result.notes.append("Medical Tests draft held for CP-BLK-01 review before dispatch.")


def _run_s4(case: Case, gateway: Gateway, correlation_id: str, result: AgentResult) -> None:
    assert_step_allowed("S4")
    result.step_id = "S4"
    result.eval_trace["bypassed_sequential_stages"] = True
    result.eval_trace["early_provisional_to"] = ATLAS_RE
    draft = {
        "title": "Provisional Facultative Referral summary",
        "referred_to": ATLAS_RE,
        "case_identifier": case.case_identifier,
        "proposer_life_assured": case.proposer_life_assured,
        "product": case.product,
        "term": case.term,
        "sum_assured": case.sum_assured,
        "occupation": case.occupation,
        "occupation_class": case.occupation_class,
        "age_last_birthday": case.age_last_birthday,
        "smoker_status": case.smoker_status,
        "trigger": (
            HAZARDOUS_OCCUPATION
            if _is_hazardous(case)
            else "Sum Assured above OPP-03 early-alert threshold"
        ),
        "best_guess_rating": "unknown",
        "dispatch": "not_available",
        "reason": (
            "IP_05 / HR-306:INT_01 — no endpoint to send the provisional summary. "
            "Draft stored on the case for underwriter review."
        ),
    }
    result.drafts["provisional_referral"] = draft
    result.notes.append(
        "Early provisional summary drafted for Atlas Re. Sequential medical wait was bypassed. "
        "Dispatch is blocked: integration is not available."
    )
    result.status = "checkpoint_pending"


def _run_s6(case: Case, gateway: Gateway, correlation_id: str, result: AgentResult) -> None:
    assert_step_allowed("S6")
    result.step_id = "S6"
    if case.mer_illegible or case.mer_password_protected:
        result.status = "escalated"
        result.escalation_queue = "Intake & Underwriting Assessment manual queue"
        result.notes.append("Source PDF is illegible or password protected.")
        _manual_task(
            gateway,
            result.case_id,
            "Extraction Error: MER unreadable",
            correlation_id,
            result,
        )
        return

    extracted = {
        "height": case.height,
        "weight": case.weight,
        "blood_pressure_sitting": case.blood_pressure_sitting,
        "tobacco_use": case.tobacco_use,
        "mer_reference": case.mer_reference,
        "condition": case.condition,
        "family_medical_history": case.family_medical_history,
    }
    if case.mer_text:
        parsed = parse_mer_text(case.mer_text)
        if not parsed.get("readable"):
            result.status = "escalated"
            result.unknowns.append("mer_text")
            result.notes.append("MER text could not be read.")
            return
        for key, value in parsed.items():
            if key in extracted and extracted[key] in (None, "") and value:
                extracted[key] = value
        result.drafts["mer_parse"] = parsed
    elif case.mer_reference:
        tool = _tool("read_document")
        path = tool["path"].replace("{docId}", case.mer_reference)
        try:
            call = gateway.call(
                tool["tool_id"], tool["method"], path, direction="read", correlation_id=correlation_id
            )
        except ToolError as exc:
            result.status = "error"
            result.notes.append(str(exc))
            _manual_task(gateway, result.case_id, str(exc), correlation_id, result)
            return
        result.reads.append({"tool": tool["tool_id"], "response": call.response})
        body = call.response or {}
        if body.get("illegible") or body.get("password_protected"):
            result.status = "escalated"
            result.notes.append("Document flagged illegible or password protected.")
            return
        parsed = parse_mer_text(body.get("text"))
        result.drafts["mer_parse"] = parsed
        for key, value in parsed.items():
            if key in extracted and extracted[key] in (None, "") and value:
                extracted[key] = value

    try:
        bmi = calculate_bmi(extracted.get("height"), extracted.get("weight"), case.bmi_auto_calculated)
    except UnitParseError as exc:
        result.status = "escalated"
        result.unknowns.extend(["height", "weight"])
        result.notes.append(f"VAL-02-01: {exc}. Crucial vitals missing or unreadable.")
        _manual_task(gateway, result.case_id, str(exc), correlation_id, result)
        return

    vitals = {
        "height": f"{bmi.height_cm} cm",
        "weight": f"{bmi.weight_kg} kg",
        "bmi_validated": bmi.bmi,
        "bmi_auto_calculated": case.bmi_auto_calculated,
        "bmi_deviation_percent": bmi.deviation_percent,
        "unit_mismatch_corrected": bmi.unit_mismatch_corrected,
        "raised_build": bmi.band() in {"overweight", "obese"},
        "blood_pressure_sitting": extracted.get("blood_pressure_sitting"),
        "tobacco_use": extracted.get("tobacco_use"),
        "mer_reference": extracted.get("mer_reference"),
        "condition": extracted.get("condition"),
        "family_medical_history": extracted.get("family_medical_history"),
        "validation": "VAL-02-01",
    }
    result.drafts["vitals"] = vitals
    result.eval_trace["val_02_01_checked"] = True
    write_tool = _tool("record_medical_results")
    path = write_tool["path"].replace("{id}", result.case_id)
    payload = {
        "height_cm": bmi.height_cm,
        "weight_kg": bmi.weight_kg,
        "bmi": bmi.bmi,
        "blood_pressure_sitting": extracted.get("blood_pressure_sitting"),
        "tobacco_use": extracted.get("tobacco_use"),
        "mer_reference": extracted.get("mer_reference"),
        "condition": extracted.get("condition"),
        "family_medical_history": extracted.get("family_medical_history"),
        "bypass_policycenter_bmi_autocalc": True,
    }
    key = gateway.idempotency_key(
        write_tool["idempotency_key"], case_id=result.case_id, payload=payload
    )
    call = gateway.call(
        write_tool["tool_id"],
        write_tool["method"],
        path,
        direction="write",
        payload=payload,
        idempotency_key=key,
        hold_write=True,
        correlation_id=correlation_id,
    )
    result.writes.append(
        {"tool": write_tool["tool_id"], "held": True, "payload": payload, "status": call.status}
    )
    result.notes.append(
        "VAL-02-01: height, weight and BMI re-computed in centimetres and kilograms; "
        "write held for CP-BLK-01."
    )
    result.status = "checkpoint_pending"


def _checkpoint_shown(case: Case, result: AgentResult) -> dict[str, Any]:
    vitals = result.drafts.get("vitals") or {}
    return {
        "height": vitals.get("height") or case.height,
        "weight": vitals.get("weight") or case.weight,
        "bmi_auto_calculated": case.bmi_auto_calculated,
        "blood_pressure_sitting": vitals.get("blood_pressure_sitting") or case.blood_pressure_sitting,
        "tobacco_use": vitals.get("tobacco_use") or case.tobacco_use,
        "mer_reference": vitals.get("mer_reference") or case.mer_reference,
        "condition": vitals.get("condition") or case.condition,
        "family_medical_history": vitals.get("family_medical_history")
        or case.family_medical_history,
        "impairment_record": case.impairment_record,
    }


def _manual_task(
    gateway: Gateway,
    case_id: str,
    message: str,
    correlation_id: str,
    result: AgentResult,
) -> None:
    tool = _tool("create_manual_task")
    path = tool["path"].replace("{id}", case_id)
    payload = {
        "queue": "Intake & Underwriting Assessment manual queue",
        "label": "Extraction Error" if "unreadable" in message.lower() or "extraction" in message.lower() else "System warning",
        "detail": message,
        "pause_automated_test_dispatch": True,
    }
    key = gateway.idempotency_key(
        tool["idempotency_key"], agent_id="BLK-01", case_id=case_id, payload=payload
    )
    try:
        gateway.call(
            tool["tool_id"],
            tool["method"],
            path,
            direction="write",
            payload=payload,
            idempotency_key=key,
            hold_write=False,
            correlation_id=correlation_id,
        )
        result.writes.append({"tool": tool["tool_id"], "payload": payload})
    except ToolError as exc:
        result.notes.append(f"Failed to write manual task: {exc}")
