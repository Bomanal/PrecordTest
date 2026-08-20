"""Eval harness for evals/cases and evals/graders.md."""

from __future__ import annotations

from typing import Any

from ..arithmetic import calculate_bmi, override_reason_is_valid
from ..case_model import Case
from ..runtime import run_agent
from ..spec_loader import precord_root
from ..tools.mock_policycenter import build_gateway, SYNTHETIC_CASES


def _load_eval_cases() -> list[dict[str, str]]:
    import csv

    path = precord_root() / "evals" / "cases.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def grade_ec01(output: dict[str, Any]) -> dict[str, Any]:
    trace = output["result"].get("eval_trace") or {}
    cues = set(trace.get("fast_track_cues_used") or [])
    required = {
        "Sum Assured",
        "Non-Medical Limit",
        "occupation",
        "age",
        "smoker status",
    }
    opened = bool(trace.get("opened_clinical_or_financial"))
    tools = {row["tool_id"] for row in output.get("tool_log") or []}
    opened_via_tools = bool(tools & {"record_medical_results", "read_document", "rating_override"})
    passed = required <= cues and not opened and not opened_via_tools
    return {
        "check_id": "R-EC-01",
        "passed": passed,
        "detail": "Fast-track used only the five preliminary cues"
        if passed
        else "Opened clinical/financial records or missed preliminary cues",
    }


def grade_ec02(output: dict[str, Any]) -> dict[str, Any]:
    trace = output["result"].get("eval_trace") or {}
    drafts = output["result"].get("drafts") or {}
    passed = bool(trace.get("bypassed_sequential_stages")) and "provisional_referral" in drafts
    return {
        "check_id": "R-EC-02",
        "passed": passed,
        "detail": "Early provisional summary drafted for Atlas Re"
        if passed
        else "Did not bypass sequential stages or missing provisional draft",
    }


def grade_val_02_01(height: str, weight: str, pc_bmi: str | None) -> dict[str, Any]:
    result = calculate_bmi(height, weight, pc_bmi)
    passed = result.requires_manual_check and result.height_cm > 0 and result.weight_kg > 0
    return {
        "check_id": "VAL-02-01",
        "passed": passed,
        "bmi": result.bmi,
        "unit_mismatch_corrected": result.unit_mismatch_corrected,
        "deviation_percent": result.deviation_percent,
    }


def grade_val_03_01(reason: str | None, override_present: bool) -> dict[str, Any]:
    if not override_present:
        return {"check_id": "VAL-03-01", "passed": True, "detail": "no override"}
    passed = override_reason_is_valid(reason)
    return {
        "check_id": "VAL-03-01",
        "passed": passed,
        "detail": "override reason present" if passed else "blocking: override reason missing or generic",
    }


def run_evals() -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    gw = build_gateway()
    fast = Case.model_validate(SYNTHETIC_CASES["LUW-FAST-01"])
    out1 = run_agent("BLK-01", fast, gateway=gw, stage="s3")
    g1 = grade_ec01(out1)
    results.append({"case_id": "EC-01", **g1, "agent_status": out1["result"]["status"]})

    gw = build_gateway()
    ref = Case.model_validate(SYNTHETIC_CASES["LUW-REF-04"])
    out2 = run_agent("BLK-01", ref, gateway=gw, stage="s4")
    g2 = grade_ec02(out2)
    results.append({"case_id": "EC-02", **g2, "agent_status": out2["result"]["status"]})

    mer = SYNTHETIC_CASES["LUW-MER-06"]
    results.append(grade_val_02_01(mer["height"], mer["weight"], mer["bmi_auto_calculated"]))

    bad = SYNTHETIC_CASES["LUW-EM-08"]
    invalid = grade_val_03_01(
        bad.get("override_reason_mandatory_field_completed"),
        bool(bad.get("underwriter_override")),
    )
    results.append(
        {
            "check_id": "VAL-03-01",
            "passed": invalid["passed"] is False,
            "detail": "detected missing override reason",
        }
    )
    gw = build_gateway()
    blocked = run_agent("BLK-02", Case.model_validate(bad), gateway=gw)
    results.append(
        {
            "check_id": "VAL-03-01-agent",
            "passed": blocked["result"]["status"] == "blocked",
            "agent_status": blocked["result"]["status"],
        }
    )

    ok = SYNTHETIC_CASES["LUW-EM-OK"]
    results.append(
        grade_val_03_01(
            ok.get("override_reason_mandatory_field_completed"),
            bool(ok.get("underwriter_override")),
        )
    )

    passed = all(row.get("passed") for row in results)
    return {"passed": passed, "results": results}
