"""Canonical names from context/ontology_nodes.csv. Variants are display only."""

from __future__ import annotations

from functools import lru_cache

from .spec_loader import ontology_nodes


@lru_cache(maxsize=1)
def canonical_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in ontology_nodes():
        canonical = row["canonical"].strip()
        mapping[canonical.lower()] = canonical
        for variant in (row.get("variants") or "").split(";"):
            variant = variant.strip()
            if variant:
                mapping[variant.lower()] = canonical
    return mapping


def canonical_name(term: str) -> str:
    if not term:
        return term
    return canonical_map().get(term.strip().lower(), term)


# Stable identifiers used in code. Values are ontology canonical names.
SUM_ASSURED = "Sum Assured"
NON_MEDICAL_LIMIT = "Non-Medical Limit"
RETENTION_LIMIT = "Retention Limit"
EXTRA_MORTALITY = "Extra Mortality"
FACULTATIVE_REFERRAL = "Facultative Referral"
MEDICAL_TESTS = "Medical Tests"
BLOOD_PRESSURE = "Blood Pressure"
FAMILY_MEDICAL_HISTORY = "Family Medical History"
HAZARDOUS_OCCUPATION = "Hazardous Occupation"
ATLAS_RE = "Atlas Re"
CASE_IDENTIFIER = "Case Identifier"
RAISED_BUILD = "Raised Build"
MEDICAL_EXAMINERS_REPORT = "Medical Examiner's Report"
