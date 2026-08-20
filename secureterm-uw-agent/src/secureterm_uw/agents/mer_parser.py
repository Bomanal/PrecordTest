"""Heuristic MER parser. LLM is optional and never used for arithmetic."""

from __future__ import annotations

import re
from typing import Any

_HEIGHT = re.compile(
    r"height\s*[:\-]?\s*(\d+\s*(?:'|ft|feet)\s*\d+\s*(?:\"|in|inch|inches)?|\d+(?:\.\d+)?\s*(?:cm|m|in|ft))",
    re.I,
)
_WEIGHT = re.compile(
    r"weight\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:kg|kgs|lb|lbs|pounds|kilograms)?)",
    re.I,
)
_BP = re.compile(r"(?:bp|blood pressure)[^\d]*(\d{2,3}\s*/\s*\d{2,3})", re.I)
_TOBACCO = re.compile(r"tobacco[^.\n]*", re.I)
_FAMILY = re.compile(r"family history\s*[:\-]?\s*([^\n.]+)", re.I)
_CONDITION = re.compile(r"condition\s*[:\-]?\s*([^\n.]+)", re.I)
_MER_ID = re.compile(r"(MER[- ]?\d+)", re.I)


def parse_mer_text(text: str | None) -> dict[str, Any]:
    if not text or not text.strip():
        return {"readable": False, "unknowns": ["mer_text"]}
    extracted: dict[str, Any] = {"readable": True, "unknowns": []}
    height = _HEIGHT.search(text)
    weight = _WEIGHT.search(text)
    bp = _BP.search(text)
    tobacco = _TOBACCO.search(text)
    family = _FAMILY.search(text)
    condition = _CONDITION.search(text)
    mer_id = _MER_ID.search(text)
    extracted["height"] = height.group(1).strip() if height else None
    extracted["weight"] = weight.group(1).strip() if weight else None
    extracted["blood_pressure_sitting"] = (
        re.sub(r"\s+", "", bp.group(1)) if bp else None
    )
    extracted["tobacco_use"] = tobacco.group(0).split(":")[-1].strip() if tobacco else None
    extracted["family_medical_history"] = family.group(1).strip() if family else None
    extracted["condition"] = condition.group(1).strip() if condition else None
    extracted["mer_reference"] = mer_id.group(1).replace(" ", "-").upper() if mer_id else None
    for key in ("height", "weight"):
        if not extracted[key]:
            extracted["unknowns"].append(key)
    return extracted
