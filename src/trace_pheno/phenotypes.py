"""Transparent AP phenotype rules used by the public synthetic tests."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Mapping

from .numeric import parse_enzyme_result


def normalize_icd(code: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(code or "").upper())


def is_ap_icd(code: object) -> bool:
    normalized = normalize_icd(code)
    return normalized == "5770" or normalized.startswith("K85")


def _present(value: object) -> bool:
    return str(value or "").strip().lower() not in {"", "nan", "none"}


def pain_assertion(row: Mapping[str, object]) -> bool | None:
    text = str(row.get("text_pain") or "").strip().lower()
    negation = str(row.get("text_negation") or "").strip().lower()
    if not text:
        return None
    if "history of" in text or "template" in str(row.get("nc_reason") or "").lower():
        return False
    if negation or text.startswith("no "):
        return False
    return "pain" in text


def imaging_assertion(row: Mapping[str, object]) -> bool | None:
    text = str(row.get("imaging") or "").strip().lower()
    if not text:
        return None
    if "no pancreatitis" in text or "negative" in text:
        return False
    return any(token in text for token in ("positive", "pancreatitis", "edema", "oedema"))


@dataclass(frozen=True)
class PhenotypeResult:
    phenotype: str
    positive: bool | None
    status: str
    evidence: dict[str, bool | None]
    score: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_ap_case(row: Mapping[str, object]) -> dict[str, PhenotypeResult]:
    icd = is_ap_icd(row.get("icd_code"))
    position = str(row.get("icd_position") or "").strip().lower()
    primary = icd and position in {"primary", "principal", "1", "01"}
    enzyme = parse_enzyme_result(row.get("enzyme_value"), row.get("ref_upper"), row.get("enzyme_unit"))
    enzyme_positive = enzyme.multiple_uln is not None and enzyme.multiple_uln >= 3.0
    pain = pain_assertion(row)
    imaging = imaging_assertion(row)
    domains = {"pain": pain, "enzyme": enzyme_positive if enzyme.status == "computable" else None, "imaging": imaging}
    positive_domains = sum(value is True for value in domains.values())
    observed_domains = sum(value is not None for value in domains.values())
    p3_positive = positive_domains >= 2
    p3_status = "computable" if p3_positive or observed_domains >= 2 else "not_computable"
    p4_score = 0.35 * (pain is True) + 0.35 * (enzyme_positive is True) + 0.30 * (imaging is True)
    p4_positive = p4_score >= 0.40
    p4_status = "computable" if p4_positive or observed_domains >= 2 else "not_computable"
    base_evidence = {"icd": icd, **domains}
    return {
        "P0": PhenotypeResult("P0", icd, "computable", base_evidence),
        "P1": PhenotypeResult("P1", primary, "computable", base_evidence),
        "P2": PhenotypeResult(
            "P2",
            icd and enzyme_positive if enzyme.status == "computable" else None,
            "computable" if enzyme.status == "computable" else "not_computable",
            base_evidence,
        ),
        "P3": PhenotypeResult("P3", p3_positive if p3_status == "computable" else None, p3_status, base_evidence),
        "P4": PhenotypeResult("P4", p4_positive if p4_status == "computable" else None, p4_status, base_evidence, p4_score),
    }

