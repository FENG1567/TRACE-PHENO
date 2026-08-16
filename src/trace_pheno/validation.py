"""Public-package validation and privacy-oriented scans."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


REGISTRY_REQUIRED = {
    "result_id", "dataset", "analysis_unit", "cohort", "phenotype", "estimand",
    "metric_name", "denominator", "estimate", "ci_lower", "ci_upper", "ci_method",
    "weighting", "source_artifact", "analysis_status",
}

FORBIDDEN_NAME_PATTERNS = (
    re.compile(r"patient|subject|hadm_id|stay_id|hospital_id", re.I),
    re.compile(r"discharge|noteevents|radiology.*text|blind_packet|raw_rating", re.I),
)
FORBIDDEN_CONTENT_PATTERNS = (
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)C:\\Users\\"),
    re.compile(r"(?i)RES-EICU-HOSP-\d+"),
)


def validate_registry(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    missing_columns = REGISTRY_REQUIRED - set(rows[0] if rows else {})
    if missing_columns:
        errors.append(f"registry missing columns: {sorted(missing_columns)}")
    for number, row in enumerate(rows, start=2):
        for field in ("result_id", "metric_name", "estimand", "source_artifact", "analysis_status"):
            if not row.get(field, "").strip():
                errors.append(f"registry row {number} missing {field}")
        if row.get("estimate", "").strip() and not row.get("denominator", "").strip():
            errors.append(f"registry row {number} has estimate without denominator")
    return errors


def scan_public_tree(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    ignored = {"CHECKSUMS.sha256", "PUBLIC_ASSET_MANIFEST.json", "PRIVACY_LICENSE_AUDIT.json"}
    for path in root.rglob("*"):
        if not path.is_file() or path.name in ignored or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        for pattern in FORBIDDEN_NAME_PATTERNS:
            if pattern.search(path.name):
                findings.append({"file": rel, "rule": "forbidden_filename", "match": pattern.pattern})
        if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".py", ".cff"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_CONTENT_PATTERNS:
            if pattern.search(text):
                findings.append({"file": rel, "rule": "forbidden_content", "match": pattern.pattern})
    return findings


def validate_json_files(root: Path) -> list[str]:
    errors = []
    for path in root.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"{path.relative_to(root)}: {exc}")
    return errors

