import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("google.adk")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adk_app.agent import _dispatch  # noqa: E402


def test_adk_dispatch_initial_request():
    output = _dispatch("BLK-REQS-CHASE UW-REQ-01 s3")
    assert output["result"]["agent_id"] == "BLK-REQS-CHASE"
    assert output["result"]["status"] == "checkpoint_pending"


def test_adk_dispatch_unknown_case():
    output = _dispatch("BLK-REQS-CHASE NOPE")
    assert "error" in output
    assert "UW-REQ-01" in output["synthetic_cases"]


def test_adk_dispatch_json_case():
    payload = {
        "agent_id": "BLK-AUTO-ARCHIVE",
        "underwriting_case_id": "UW-DECLINE-09",
        "underwriting_decision": "Decline",
        "status": "Decision pending",
        "policy_bound": False,
    }
    output = _dispatch(json.dumps(payload))
    assert output["result"]["eval_trace"]["archived"] is False
