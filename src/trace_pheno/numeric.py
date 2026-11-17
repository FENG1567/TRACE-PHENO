"""Locale-tolerant numeric and enzyme-result parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass


NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
UNIT_RE = re.compile(r"(?i)\b(?:IU|U|units?)\s*/\s*L\b")


@dataclass(frozen=True)
class EnzymeResult:
    value: float | None
    reference_upper: float | None
    unit: str | None
    multiple_uln: float | None
    status: str


def parse_number(value: object) -> float | None:
    """Extract one finite decimal/scientific-notation number from a value."""
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    match = NUMBER_RE.search(text)
    if not match:
        return None
    try:
        number = float(match.group(0))
    except ValueError:
        return None
    return number if number == number and abs(number) != float("inf") else None


def normalize_enzyme_unit(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return "U/L" if UNIT_RE.search(text) else None


def parse_enzyme_result(value: object, reference_upper: object, unit: object) -> EnzymeResult:
    measured = parse_number(value)
    upper = parse_number(reference_upper)
    normalized_unit = normalize_enzyme_unit(unit)
    if measured is None:
        return EnzymeResult(None, upper, normalized_unit, None, "missing_value")
    if normalized_unit is None:
        return EnzymeResult(measured, upper, None, None, "unsupported_unit")
    if upper is None or upper <= 0:
        return EnzymeResult(measured, upper, normalized_unit, None, "missing_uln")
    return EnzymeResult(measured, upper, normalized_unit, measured / upper, "computable")

