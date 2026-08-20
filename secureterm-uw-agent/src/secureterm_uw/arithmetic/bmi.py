"""Deterministic BMI. Never a model call (BUILD.md)."""

from __future__ import annotations

import re
from dataclasses import dataclass


class UnitParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedMeasure:
    value: float
    unit: str
    raw: str


@dataclass(frozen=True)
class BmiResult:
    height_cm: float
    weight_kg: float
    bmi: float
    height_raw: str
    weight_raw: str
    unit_mismatch_corrected: bool
    policycenter_bmi: float | None
    deviation_percent: float | None
    requires_manual_check: bool

    def band(self) -> str:
        if self.bmi >= 30:
            return "obese"
        if self.bmi >= 25:
            return "overweight"
        if self.bmi >= 18.5:
            return "standard"
        return "underweight"


_FEET_INCHES = re.compile(
    r"""
    ^\s*
    (?:(?P<ft>\d+(?:\.\d+)?)\s*(?:'|ft|feet|foot)\s*)
    (?:(?P<inch>\d+(?:\.\d+)?)\s*(?:"|in|inch|inches)?)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
_NUMBER_UNIT = re.compile(
    r"^\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z\"']+)?\s*$"
)
_IMPERIAL_PAIR = re.compile(r"^\s*(\d+)\s*[-/]\s*(\d+)\s*$")


def parse_height_cm(raw: str | None) -> ParsedMeasure:
    if raw is None or not str(raw).strip():
        raise UnitParseError("height is unknown")
    text = str(raw).strip()
    feet = _FEET_INCHES.match(text)
    if feet:
        ft = float(feet.group("ft"))
        inch = float(feet.group("inch") or 0)
        cm = (ft * 12 + inch) * 2.54
        return ParsedMeasure(cm, "cm", text)
    pair = _IMPERIAL_PAIR.match(text)
    if pair:
        cm = (int(pair.group(1)) * 12 + int(pair.group(2))) * 2.54
        return ParsedMeasure(cm, "cm", text)
    match = _NUMBER_UNIT.match(text)
    if not match:
        raise UnitParseError(f"unreadable height: {text}")
    value = float(match.group("num"))
    unit = (match.group("unit") or "cm").lower()
    if unit in {"cm", "centimeter", "centimetre", "centimeters", "centimetres"}:
        return ParsedMeasure(value, "cm", text)
    if unit in {"m", "meter", "metre", "meters", "metres"}:
        return ParsedMeasure(value * 100, "cm", text)
    if unit in {"in", "inch", "inches", '"'}:
        return ParsedMeasure(value * 2.54, "cm", text)
    if unit in {"ft", "feet", "foot", "'"}:
        return ParsedMeasure(value * 30.48, "cm", text)
    raise UnitParseError(f"unknown height unit in {text}")


def parse_weight_kg(raw: str | None) -> ParsedMeasure:
    if raw is None or not str(raw).strip():
        raise UnitParseError("weight is unknown")
    text = str(raw).strip()
    match = _NUMBER_UNIT.match(text)
    if not match:
        raise UnitParseError(f"unreadable weight: {text}")
    value = float(match.group("num"))
    unit = (match.group("unit") or "kg").lower()
    if unit in {"kg", "kgs", "kilogram", "kilograms"}:
        return ParsedMeasure(value, "kg", text)
    if unit in {"lb", "lbs", "pound", "pounds"}:
        return ParsedMeasure(value * 0.45359237, "kg", text)
    raise UnitParseError(f"unknown weight unit in {text}")


def calculate_bmi(
    height_raw: str | None,
    weight_raw: str | None,
    policycenter_bmi: str | float | None = None,
) -> BmiResult:
    height = parse_height_cm(height_raw)
    weight = parse_weight_kg(weight_raw)
    height_m = height.value / 100.0
    if height_m <= 0 or weight.value <= 0:
        raise UnitParseError("height and weight must be positive")
    bmi = round(weight.value / (height_m * height_m), 2)
    unit_mismatch = bool(
        re.search(r"ft|feet|'|in|lb|pound", f"{height.raw} {weight.raw}", re.I)
    )
    pc_value: float | None = None
    if policycenter_bmi not in (None, ""):
        try:
            pc_value = float(str(policycenter_bmi).strip())
        except ValueError:
            pc_value = None
    deviation = None
    if pc_value is not None and pc_value > 0:
        deviation = abs(bmi - pc_value) / pc_value * 100.0
    requires_check = True  # VAL-02-01: always check height/weight/BMI
    return BmiResult(
        height_cm=round(height.value, 2),
        weight_kg=round(weight.value, 2),
        bmi=bmi,
        height_raw=height.raw,
        weight_raw=weight.raw,
        unit_mismatch_corrected=unit_mismatch,
        policycenter_bmi=pc_value,
        deviation_percent=None if deviation is None else round(deviation, 2),
        requires_manual_check=requires_check,
    )
