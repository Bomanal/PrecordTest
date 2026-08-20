import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("google.adk")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adk_app.agent import _dispatch  # noqa: E402


def test_adk_dispatch_fast_track():
    output = _dispatch("BLK-01 LUW-FAST-01 s3")
    assert output["result"]["agent_id"] == "BLK-01"
    assert output["result"]["eval_trace"]["s3_route"] == "non_medical_fast_track"


def test_adk_dispatch_unknown_case():
    output = _dispatch("BLK-01 NOPE")
    assert "error" in output
    assert "LUW-FAST-01" in output["synthetic_cases"]


def test_adk_dispatch_json_case():
    payload = {
        "agent_id": "BLK-02",
        "case_identifier": "LUW-EM-08",
        "underwriter_override": "100%",
        "override_reason_mandatory_field_completed": "",
        "rating_engine_suggested_em": "75%",
        "sum_assured": 12_000_000,
        "occupation": "Engineer",
        "occupation_class": "standard",
    }
    output = _dispatch(json.dumps(payload))
    assert output["result"]["status"] == "blocked"
