"""Shared case object. Field names match schemas/case.schema.json (ontology canonical)."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

from .spec_loader import case_schema


class Case(BaseModel):
    """Case fields used by both agents. Extra keys from PolicyCenter are kept."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_identifier: str | None = None
    proposer_life_assured: str | None = None
    product: str | None = None
    term: str | None = None
    sum_assured: float | None = None
    declared_annual_income: float | None = None
    income_proof_status: str | None = None
    applied_sum_insured: float | None = None
    hlv_justified_amount: float | None = None
    existing_in_force_cover_other_insurers: float | None = None
    aggregate_cover_post_issue: float | None = None
    occupation: str | None = None
    occupation_class: str | None = None
    employer: str | None = None
    financial_underwriter_notes: str | None = None
    height: str | None = None
    weight: str | None = None
    bmi_auto_calculated: str | None = None
    blood_pressure_sitting: str | None = None
    tobacco_use: str | None = None
    mer_reference: str | None = None
    condition: str | None = None
    family_medical_history: str | None = None
    impairment_record: str | None = None
    decision_status_header: str | None = None
    rating_engine_suggested_em: str | None = None
    underwriter_override: str | None = None
    referred_to: str | None = None
    reinsurer_terms: str | None = None
    decision: str | None = None
    override_reason_mandatory_field_completed: str | None = Field(default=None)
    header_status: str | None = None
    header_sum_insured: float | None = None
    riders: str | None = None
    rating: str | None = None
    annual_premium: float | None = None
    premium_mode: str | None = None
    referral_outcome: str | None = None
    evidence_relied_upon: str | None = None
    age_last_birthday: int | None = None
    smoker_status: str | None = None
    mer_text: str | None = None
    mer_illegible: bool = False
    mer_password_protected: bool = False
    application_received_at: str | None = None

    def sum_insured_conflict(self) -> bool:
        """OI-04: conflicting recorded Sum Assured values are a halt, not a pick."""
        values = [
            v
            for v in (self.sum_assured, self.applied_sum_insured, self.header_sum_insured)
            if v is not None
        ]
        if len(values) < 2:
            return False
        return max(values) - min(values) > 0.01

    def preliminary_cues(self) -> dict[str, Any]:
        """S3 fast-track cues only. Clinical and financial evidence are excluded."""
        return {
            "sum_assured": self.sum_assured,
            "occupation": self.occupation,
            "occupation_class": self.occupation_class,
            "age_last_birthday": self.age_last_birthday,
            "smoker_status": self.smoker_status or self.tobacco_use,
        }

    def blk01_input(self) -> dict[str, Any]:
        return self.model_dump(
            include={
                "blood_pressure_sitting",
                "bmi_auto_calculated",
                "condition",
                "family_medical_history",
                "height",
                "impairment_record",
                "mer_reference",
                "tobacco_use",
                "weight",
            }
        )

    def blk02_input(self) -> dict[str, Any]:
        return self.model_dump(
            include={
                "case_identifier",
                "decision",
                "decision_status_header",
                "override_reason_mandatory_field_completed",
                "product",
                "proposer_life_assured",
                "rating_engine_suggested_em",
                "referred_to",
                "reinsurer_terms",
                "sum_assured",
                "term",
                "underwriter_override",
            }
        )


def validate_against_case_schema(payload: dict[str, Any]) -> list[str]:
    schema = case_schema()
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(payload)]
