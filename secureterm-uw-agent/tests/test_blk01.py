from secureterm_uw.agents.base import NEVER_AUTOMATE_STEPS
from secureterm_uw.case_model import Case
from secureterm_uw.runtime import run_agent
from secureterm_uw.tools.mock_policycenter import SYNTHETIC_CASES, build_gateway


def test_s2_s11_s15_are_never_automated():
    assert NEVER_AUTOMATE_STEPS == {"S2", "S11", "S15"}


def test_fast_track_uses_preliminary_cues_only():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-FAST-01"])
    output = run_agent("BLK-01", case, gateway=gateway, stage="s3")
    trace = output["result"]["eval_trace"]
    assert set(trace["fast_track_cues_used"]) >= {
        "Sum Assured",
        "Non-Medical Limit",
        "occupation",
        "age",
        "smoker status",
    }
    assert trace["opened_clinical_or_financial"] is False
    assert output["result"]["drafts"]["fast_track"] is True
    tool_ids = {row["tool_id"] for row in output["tool_log"]}
    assert "read_document" not in tool_ids
    assert "record_medical_results" not in tool_ids


def test_early_referral_bypasses_sequential_path():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-REF-04"])
    output = run_agent("BLK-01", case, gateway=gateway, stage="s4")
    result = output["result"]
    assert result["eval_trace"]["bypassed_sequential_stages"] is True
    draft = result["drafts"]["provisional_referral"]
    assert draft["referred_to"] == "Atlas Re"
    assert draft["dispatch"] == "not_available"


def test_mer_bmi_write_is_held_for_checkpoint():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-MER-06"])
    output = run_agent("BLK-01", case, gateway=gateway, stage="s6")
    result = output["result"]
    assert result["status"] == "checkpoint_pending"
    assert result["eval_trace"]["val_02_01_checked"] is True
    vitals = result["drafts"]["vitals"]
    assert vitals["unit_mismatch_corrected"] is True
    assert output["held_writes"]
    assert output["checkpoint"]["checkpoint_id"] == "CP-BLK-01"


def test_conflicting_sum_assured_halts_on_oi04():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-1010"])
    output = run_agent("BLK-01", case, gateway=gateway, stage="s3")
    assert output["result"]["status"] == "open_item"
    assert "OI-04" in output["result"]["open_items"]
