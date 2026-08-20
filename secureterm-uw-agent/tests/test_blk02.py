from secureterm_uw.case_model import Case
from secureterm_uw.checkpoints import STORE
from secureterm_uw.runtime import run_agent
from secureterm_uw.tools.mock_policycenter import SYNTHETIC_CASES, build_gateway


def test_missing_override_reason_blocks_write():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-EM-08"])
    output = run_agent("BLK-02", case, gateway=gateway)
    assert output["result"]["status"] == "blocked"
    assert output["result"]["eval_trace"]["val_03_01"] == "fail"
    assert output["held_writes"] == []


def test_valid_override_is_held_not_dispatched():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-EM-OK"])
    output = run_agent("BLK-02", case, gateway=gateway)
    assert output["result"]["status"] in {"checkpoint_pending", "open_item"}
    assert output["result"]["eval_trace"]["val_03_01"] == "pass"
    tools = {row["tool_id"] for row in output["held_writes"]}
    assert "rating_override" in tools
    assert output["checkpoint"]["checkpoint_id"] == "CP-BLK-02"


def test_retention_limit_is_not_invented():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-EM-OK"])
    output = run_agent("BLK-02", case, gateway=gateway)
    assert "OI-01" in output["result"]["open_items"]
    treaty = output["result"]["drafts"]["treaty_limits"]
    assert treaty["retention_limit"] is None


def test_checkpoint_approve_releases_writes():
    gateway = build_gateway()
    case = Case.model_validate(SYNTHETIC_CASES["LUW-EM-OK"])
    output = run_agent("BLK-02", case, gateway=gateway)
    run_id = output["checkpoint"]["checkpoint_run_id"]
    STORE.resolve(
        run_id,
        "approve",
        reason_code=None,
        reviewer="uw-test",
        gateway=gateway,
        correlation_id="test",
    )
    assert gateway.held_writes == []
    assert any(call.tool_id == "rating_override" and not call.held for call in gateway.executed)
