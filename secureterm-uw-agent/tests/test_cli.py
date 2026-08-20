from secureterm_uw.cli import main
from secureterm_uw.tools.mock_policycenter import SYNTHETIC_CASES


def test_eval_cli_exits_zero(capsys):
    assert main(["eval"]) == 0
    captured = capsys.readouterr()
    report = __import__("json").loads(captured.out)
    assert report["passed"] is True
    assert captured.err == ""


def test_run_cli_emits_json_only(capsys):
    assert main(["run", "--agent", "BLK-01", "--synthetic", "LUW-FAST-01", "--stage", "s3"]) == 0
    captured = capsys.readouterr()
    body = __import__("json").loads(captured.out)
    assert body["result"]["agent_id"] == "BLK-01"
    assert captured.err == ""


def test_cases_cli_lists_synthetics(capsys):
    assert main(["cases"]) == 0
    body = __import__("json").loads(capsys.readouterr().out)
    assert "LUW-FAST-01" in body["synthetic_cases"]
    assert set(body["synthetic_cases"]) == set(SYNTHETIC_CASES)
