from medrecs_uw.case_model import Case
from medrecs_uw.runtime import run_agent
from medrecs_uw.tools.catalog import TOOLS, UNAVAILABLE_TOOLS
from medrecs_uw.tools.mock_systems import SYNTHETIC_CASES, build_gateway


def test_email_extracts_case_id_and_timeline():
    gateway = build_gateway()
    output = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-MAIL-04"]),
        gateway=gateway,
        stage="s5",
    )
    parsed = output["result"]["drafts"]["email_parse"]
    assert parsed["underwriting_case_id"] == "UW-MAIL-04"
    assert parsed["timeline"]
    assert parsed["confidence"] == "high"
    assert output["result"]["sub_agents"][0]["agent_id"] == "BLK-INTAKE-MONITOR.1"


def test_unparsed_email_retains_status():
    gateway = build_gateway()
    output = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-MAIL-05"]),
        gateway=gateway,
        stage="s5",
    )
    result = output["result"]
    assert result["status"] == "escalated"
    assert result["eval_trace"]["status_retained"] == "Awaiting records"


def test_vault_match_advances_in_review_without_int04():
    gateway = build_gateway()
    output = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-VAULT-06"]),
        gateway=gateway,
        stage="s9",
    )
    result = output["result"]
    assert result["eval_trace"]["status_advanced"] == "In Review"
    assert result["eval_trace"]["int_04_used"] is False
    assert result["sub_agents"][0]["agent_id"] == "BLK-INTAKE-MONITOR.2"
    assert all(row.get("integration_point_id") != "INT_04" for row in TOOLS)
    assert any(row.get("integration_point_id") == "INT_04" for row in UNAVAILABLE_TOOLS)
    assert gateway.store["UW-VAULT-06"]["status"] == "In Review"


def test_vault_mismatch_does_not_auto_advance():
    gateway = build_gateway()
    output = run_agent(
        "BLK-INTAKE-MONITOR",
        Case.model_validate(SYNTHETIC_CASES["UW-VAULT-07"]),
        gateway=gateway,
        stage="s9",
    )
    result = output["result"]
    assert result["status"] == "escalated"
    assert result["eval_trace"]["status_retained"] == "Awaiting records"
    assert gateway.store["UW-VAULT-07"]["status"] == "Awaiting records"
