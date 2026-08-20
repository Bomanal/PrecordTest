"""In-process PolicyCenter + Atlas Re stand-in for local runs and evals.

Synthetic only. Grid bands and retention figures here are fixtures, not
client NML or Retention Limit (those are OI-02 and OI-01).
"""

from __future__ import annotations

import copy
from typing import Any

from .gateway import Gateway, ToolCall, ToolError


SYNTHETIC_CASES: dict[str, dict[str, Any]] = {
    "LUW-FAST-01": {
        "case_identifier": "LUW-FAST-01",
        "proposer_life_assured": "Synthetic Proposer A",
        "product": "SecureTerm",
        "term": "20 years",
        "sum_assured": 5_000_000,
        "applied_sum_insured": 5_000_000,
        "occupation": "Accountant",
        "occupation_class": "standard",
        "age_last_birthday": 32,
        "smoker_status": "non-smoker",
        "tobacco_use": "never",
        "application_received_at": "2026-01-10T09:00:00Z",
    },
    "LUW-REF-04": {
        "case_identifier": "LUW-REF-04",
        "proposer_life_assured": "Synthetic Proposer B",
        "product": "SecureTerm",
        "term": "25 years",
        "sum_assured": 30_000_000,
        "applied_sum_insured": 30_000_000,
        "occupation": "merchant navy",
        "occupation_class": "hazardous",
        "age_last_birthday": 44,
        "smoker_status": "smoker",
        "tobacco_use": "current",
        "application_received_at": "2026-01-11T09:00:00Z",
    },
    "LUW-MER-06": {
        "case_identifier": "LUW-MER-06",
        "proposer_life_assured": "Synthetic Proposer C",
        "product": "SecureTerm",
        "term": "15 years",
        "sum_assured": 8_000_000,
        "applied_sum_insured": 8_000_000,
        "occupation": "Teacher",
        "occupation_class": "standard",
        "age_last_birthday": 38,
        "smoker_status": "non-smoker",
        "height": "5'10\"",
        "weight": "198 lbs",
        "bmi_auto_calculated": "72.1",
        "blood_pressure_sitting": "128/82",
        "tobacco_use": "never",
        "mer_reference": "MER-9001",
        "mer_text": (
            "Medical Examiner's Report MER-9001. Height 5 ft 10 in. "
            "Weight 198 pounds. BP sitting 128/82. Tobacco: never. "
            "Condition: none disclosed. Family history: father MI at 62."
        ),
        "condition": None,
        "family_medical_history": None,
        "impairment_record": None,
    },
    "LUW-EM-08": {
        "case_identifier": "LUW-EM-08",
        "proposer_life_assured": "Synthetic Proposer D",
        "product": "SecureTerm",
        "term": "20 years",
        "sum_assured": 12_000_000,
        "rating_engine_suggested_em": "75%",
        "underwriter_override": "100%",
        "override_reason_mandatory_field_completed": "",
        "occupation": "Engineer",
        "occupation_class": "standard",
        "age_last_birthday": 41,
        "smoker_status": "non-smoker",
        "decision_status_header": "In assessment",
    },
    "LUW-EM-OK": {
        "case_identifier": "LUW-EM-OK",
        "proposer_life_assured": "Synthetic Proposer E",
        "product": "SecureTerm",
        "term": "20 years",
        "sum_assured": 12_000_000,
        "rating_engine_suggested_em": "75%",
        "underwriter_override": "125%",
        "override_reason_mandatory_field_completed": (
            "Type 2 Diabetes Mellitus with HbA1c 7.8; build overweight"
        ),
        "occupation": "Engineer",
        "occupation_class": "standard",
        "age_last_birthday": 41,
        "smoker_status": "non-smoker",
        "height": "172 cm",
        "weight": "88 kg",
        "condition": "Type 2 Diabetes Mellitus",
        "decision_status_header": "In assessment",
    },
    "LUW-1010": {
        "case_identifier": "LUW-1010",
        "proposer_life_assured": "Synthetic Proposer F",
        "product": "SecureTerm",
        "term": "20 years",
        "sum_assured": 10_000_000,
        "applied_sum_insured": 12_000_000,
        "header_sum_insured": 10_000_000,
        "occupation": "Clerk",
        "occupation_class": "standard",
        "age_last_birthday": 35,
        "smoker_status": "non-smoker",
    },
}

# Fixture grid — labelled synthetic. Not client NML (OI-02).
SYNTHETIC_GRID = {
    "source": "synthetic_fixture",
    "open_item": "OI-02",
    "bands": [
        {"max_age": 35, "max_sum_assured": 7_500_000, "nml_eligible": True, "tests": []},
        {
            "max_age": 45,
            "max_sum_assured": 15_000_000,
            "nml_eligible": False,
            "tests": ["MER", "Blood Profile"],
        },
        {
            "max_age": 60,
            "max_sum_assured": 50_000_000,
            "nml_eligible": False,
            "tests": ["MER", "Blood Profile", "Resting Electrocardiogram"],
        },
    ],
}

# Treaty lookup returns unknown: OI-01 is blocking and must not be invented.
SYNTHETIC_TREATY = {
    "source": "synthetic_fixture",
    "open_item": "OI-01",
    "retention_limit": None,
    "automatic_acceptance_limit": None,
    "reinsurer": "Atlas Re",
}


class MockGateway(Gateway):
    def __init__(self) -> None:
        super().__init__()
        self.store: dict[str, dict[str, Any]] = copy.deepcopy(SYNTHETIC_CASES)
        self.orders: dict[str, dict[str, Any]] = {}
        self.results: dict[str, dict[str, Any]] = {}
        self.overrides: dict[str, dict[str, Any]] = {}
        self.referrals: dict[str, dict[str, Any]] = {}
        self.tasks: list[dict[str, Any]] = []

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        idempotency_key: str | None,
        correlation_id: str,
        timeout_s: int | None,
    ) -> Any:
        del timeout_s
        if method == "GET" and path.startswith("/underwriting/medical-grid"):
            return self._grid(path)
        if method == "GET" and path == "/reinsurance/treaty-limits":
            return copy.deepcopy(SYNTHETIC_TREATY)
        if method == "GET" and path.startswith("/documents/"):
            doc_id = path.rsplit("/", 1)[-1]
            for case in self.store.values():
                if case.get("mer_reference") == doc_id:
                    return {
                        "docId": doc_id,
                        "text": case.get("mer_text"),
                        "illegible": case.get("mer_illegible", False),
                        "password_protected": case.get("mer_password_protected", False),
                    }
            raise ToolError(f"document {doc_id} not found", 404)
        if method == "POST" and path.endswith("/medical/tests"):
            case_id = path.split("/")[2]
            self.orders[case_id] = payload or {}
            return {"ordered": True, "case_identifier": case_id, "tests": (payload or {}).get("tests")}
        if method == "POST" and path.endswith("/medical/results"):
            case_id = path.split("/")[2]
            self.results[case_id] = payload or {}
            self.store.setdefault(case_id, {}).update(payload or {})
            return {"recorded": True, "case_identifier": case_id}
        if method == "POST" and path.endswith("/rating/override"):
            case_id = path.split("/")[2]
            self.overrides[case_id] = payload or {}
            return {"accepted": True, "case_identifier": case_id}
        if method == "POST" and path == "/reinsurance/referrals":
            case_id = (payload or {}).get("case_identifier", "unknown")
            referral_id = f"REF-{len(self.referrals) + 1:04d}"
            self.referrals[referral_id] = payload or {}
            return {"referral_id": referral_id, "status": "draft_submitted", "case_identifier": case_id}
        if method == "POST" and path.endswith("/tasks"):
            self.tasks.append(payload or {})
            return {"task_created": True}
        raise ToolError(f"unmapped mock path {method} {path}", 404)

    def _grid(self, path: str) -> dict[str, Any]:
        from urllib.parse import parse_qs, urlparse

        query = parse_qs(urlparse(path).query)
        age = int((query.get("age") or ["0"])[0] or 0)
        sum_insured = float((query.get("sumInsured") or ["0"])[0] or 0)
        chosen = SYNTHETIC_GRID["bands"][-1]
        for band in SYNTHETIC_GRID["bands"]:
            if age <= band["max_age"] and sum_insured <= band["max_sum_assured"]:
                chosen = band
                break
        tests = list(chosen["tests"])
        return {
            "source": "synthetic_fixture",
            "open_item": "OI-02",
            "age": age,
            "sumInsured": sum_insured,
            "nml_eligible": chosen["nml_eligible"] and sum_insured <= chosen["max_sum_assured"],
            "nml_band": f"age<={chosen['max_age']};sum<={chosen['max_sum_assured']}",
            "required_tests": tests,
        }


def build_gateway(settings=None) -> Gateway:
    from ..config import get_settings

    cfg = settings or get_settings()
    if cfg.mock_gateway:
        return MockGateway()
    return Gateway(settings=cfg)
