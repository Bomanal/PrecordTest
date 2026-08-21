from medrecs_uw.case_model import Case
from medrecs_uw.runtime import run_agent
from medrecs_uw.tools.mock_systems import SYNTHETIC_CASES, build_gateway


def test_bound_policy_is_archived():
    gateway = build_gateway()
    output = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-BOUND-08"]),
        gateway=gateway,
    )
    result = output["result"]
    assert result["eval_trace"]["archived"] is True
    archive = result["drafts"]["archive"]
    assert archive["underwriting_case_id"] == "UW-BOUND-08"
    assert archive["face_amount"] == 750_000
    assert archive["touches"] == 4
    assert archive["cycle_time"]
    assert "UW-BOUND-08" in gateway.archives
    assert result["eval_trace"]["int_03_used"] is False


def test_decline_is_not_archived():
    gateway = build_gateway()
    output = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-DECLINE-09"]),
        gateway=gateway,
    )
    result = output["result"]
    assert result["eval_trace"]["archived"] is False
    assert result["eval_trace"]["reason"] == "alternative_outcome"
    assert gateway.archives == {}
    assert gateway.store["UW-DECLINE-09"]["status"] != "Closed"


def test_archive_failure_leaves_case_open_and_drafts_ticket():
    gateway = build_gateway()
    output = run_agent(
        "BLK-AUTO-ARCHIVE",
        Case.model_validate(SYNTHETIC_CASES["UW-FAIL-10"]),
        gateway=gateway,
    )
    result = output["result"]
    assert result["eval_trace"]["archived"] is False
    assert result["drafts"]["it_ticket"]["leave_case_open"] is True
    assert gateway.store["UW-FAIL-10"]["status"] == "Bound"
    assert output["checkpoint"]["checkpoint_id"] == "CP-BLK-AUTO-ARCHIVE"
