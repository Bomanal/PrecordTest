"""Shared case object. Field names match schemas/case.schema.json."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

from .spec_loader import case_schema


class Case(BaseModel):
    """Case fields from the shared schema, plus extra keys the mock systems carry.

    Extra keys are synthetic extensions: the per-agent in/out schemas are empty
    objects, and context/surface registers are not in this Precord package.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    underwriting_case_id: str | None = None
    case: str | None = None
    status: str | None = None
    aging: str | None = None
    risk_classification: str | None = None
    underwriting_decision: str | None = None

    assigned_underwriter: str | None = None
    product_type: str | None = None
    face_amount: float | None = None
    cycle_time: str | None = None
    touches: int | None = None
    application_received_at: str | None = None
    bound_at: str | None = None
    policy_bound: bool = False
    policy_issued: bool = False
    attending_physician_statement_required: bool = False
    laboratory_report_required: bool = False
    documents_received: list[str] = Field(default_factory=list)
    inbound_email: dict[str, Any] | None = None
    vault_documents: list[dict[str, Any]] = Field(default_factory=list)
    applicant_name: str | None = None
    force_archive_failure: bool = False
    force_checkpoint: bool = False
    extraction_confidence: str | None = None

    @property
    def case_id(self) -> str:
        return self.underwriting_case_id or self.case or "unknown"

    def received_types(self) -> set[str]:
        return {str(item).strip().lower() for item in self.documents_received if item}


def validate_against_case_schema(payload: dict[str, Any]) -> list[str]:
    schema = case_schema()
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(payload)]
