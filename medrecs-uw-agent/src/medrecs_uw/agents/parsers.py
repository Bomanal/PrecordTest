"""Deterministic extraction of underwriting_case_id and delivery timelines."""

from __future__ import annotations

import re
from typing import Any

CASE_ID_RE = re.compile(r"\b(UW[-_ ]?\d{4}[-_ ]?\d{2,6}|UW-[A-Z]+-\d+)\b", re.IGNORECASE)
DAYS_RE = re.compile(
    r"(?:expected|eta|timeline|deliver(?:y|ed)?|send|arrive|ready).{0,48}?(\d{1,3})\s+days",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"(?:expected|eta|by|on|deliver(?:y|ed)?).{0,24}(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


def parse_email(message: dict[str, Any] | None) -> dict[str, Any]:
    if not message:
        return {
            "readable": False,
            "confidence": "low",
            "underwriting_case_id": None,
            "timeline": None,
            "reason": "no inbound email",
        }
    blob = " ".join(
        str(message.get(key) or "") for key in ("subject", "body", "text")
    )
    match = CASE_ID_RE.search(blob)
    case_id = match.group(1).upper().replace(" ", "").replace("_", "-") if match else None
    days = DAYS_RE.search(blob)
    date = DATE_RE.search(blob)
    timeline = None
    if days:
        timeline = f"{days.group(1)} days"
    elif date:
        timeline = date.group(1)
    confidence = "high" if case_id and timeline else ("medium" if case_id else "low")
    return {
        "readable": bool(blob.strip()),
        "confidence": confidence,
        "underwriting_case_id": case_id,
        "timeline": timeline,
        "subject": message.get("subject"),
        "from": message.get("from"),
        "message_id": message.get("id"),
    }


def classify_document(document: dict[str, Any]) -> str | None:
    declared = str(document.get("document_type") or document.get("type") or "").lower()
    if "lab" in declared:
        return "laboratory_report"
    if "aps" in declared or "physician" in declared or "attending" in declared:
        return "attending_physician_statement"
    name = str(document.get("name") or document.get("filename") or "").lower()
    if "lab" in name or "lipid" in name:
        return "laboratory_report"
    if "aps" in name or "physician" in name:
        return "attending_physician_statement"
    return declared or None


def documents_match_case(
    documents: list[dict[str, Any]],
    case_id: str,
    applicant_name: str | None,
) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for doc in documents:
        doc_case = str(doc.get("case_id") or doc.get("underwriting_case_id") or "").upper()
        doc_type = classify_document(doc)
        applicant = str(doc.get("applicant_name") or "")
        if doc_case and doc_case != case_id.upper():
            mismatches.append("case_id")
            continue
        if applicant_name and applicant and applicant.strip().lower() != applicant_name.strip().lower():
            mismatches.append("applicant_name")
            continue
        if not doc_type:
            mismatches.append("document_type")
            continue
        matched.append({**doc, "canonical_type": doc_type})
    return {
        "matched": matched,
        "mismatches": sorted(set(mismatches)),
        "verified": bool(matched) and not mismatches,
    }
