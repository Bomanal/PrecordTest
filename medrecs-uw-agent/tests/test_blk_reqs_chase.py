from medrecs_uw.agents.base import NEVER_AUTOMATE_STEPS, assert_step_allowed, AutomationForbidden
from medrecs_uw.case_model import Case
from medrecs_uw.runtime import run_agent
from medrecs_uw.tools.mock_systems import SYNTHETIC_CASES, build_gateway


def test_never_automate_clinical_and_decision_steps():
    assert {"S1", "S2", "S4", "S6", "S7", "S10", "S11", "S12", "S14"} <= NEVER_AUTOMATE_STEPS
    for step in ("S10", "S11", "S14"):
        try:
            assert_step_allowed(step)
            raise AssertionError(f"{step} should be forbidden")
        except AutomationForbidden:
            pass


def test_s3_drafts_request_and_holds_for_checkpoint():
    gateway = build_gateway()
    output = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-REQ-01"]),
        gateway=gateway,
        stage="s3",
    )
    result = output["result"]
    assert result["status"] == "checkpoint_pending"
    assert result["step_id"] == "S3"
    assert "attending_physician_statement" in result["drafts"]["email"]["requirements"]
    assert output["held_writes"]
    assert output["checkpoint"]["checkpoint_id"] == "CP-BLK-REQS-CHASE"
    assert result["eval_trace"]["never_wrote_underwriting_decision"] is True


def test_duplicate_request_is_blocked():
    gateway = build_gateway()
    output = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-REQ-02"]),
        gateway=gateway,
        stage="s3",
    )
    assert output["result"]["eval_trace"]["duplicate_request_prevented"] is True
    assert output["held_writes"] == []
    assert output["result"]["status"] == "completed"


def test_s8_escalates_unknown_aging_threshold():
    gateway = build_gateway()
    output = run_agent(
        "BLK-REQS-CHASE",
        Case.model_validate(SYNTHETIC_CASES["UW-CHASE-03"]),
        gateway=gateway,
        stage="s8",
    )
    result = output["result"]
    assert result["status"] == "escalated"
    assert "chase_aging_threshold" in result["unknowns"]
    assert result["eval_trace"]["chase_threshold"] == "unknown"
