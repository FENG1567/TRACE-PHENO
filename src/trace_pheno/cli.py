"""Command-line entry point for the public reproducibility package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .aki_demo import creatinine_rule, urine_rule
from .cards import build_cards
from .equivalence import p3_p4_equivalence
from .phenotypes import evaluate_ap_case
from .validation import scan_public_tree, validate_json_files, validate_registry


ROOT = Path(__file__).resolve().parents[2]


def synthetic() -> int:
    with (ROOT / "data" / "synthetic" / "AP_synthetic_cases.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = [{"case_id": row["case_id"], "results": {key: value.to_dict() for key, value in evaluate_ap_case(row).items()}} for row in rows]
    aki = {
        "delta_48h": creatinine_rule([0.9, 1.1, 1.3], [0, 12, 30]),
        "ratio_7d": creatinine_rule([1.0, 1.0, 1.6], [0, 96, 150]),
        "urine_6h": urine_rule([20] * 6, 70),
        "missing_weight": urine_rule([20] * 6, None),
    }
    out = ROOT / "artifacts" / "synthetic_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"ap": results, "aki": aki, "clinical_claims": False}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


def equivalence() -> int:
    result = p3_p4_equivalence()
    out = ROOT / "artifacts" / "p3_p4_equivalence.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"P3/P4 equivalent: {result['equivalent']}")
    return 0 if result["equivalent"] else 1


def validate() -> int:
    errors = validate_registry(ROOT / "results" / "manuscript_result_registry.csv")
    errors += validate_json_files(ROOT / "configs")
    errors += validate_json_files(ROOT / "schemas")
    findings = scan_public_tree(ROOT)
    report = {"status": "PASS" if not errors and not findings else "FAIL", "errors": errors, "privacy_findings": findings}
    out = ROOT / "artifacts" / "validation_report.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("synthetic", "equivalence", "cards", "validate", "all"))
    args = parser.parse_args()
    actions = {
        "synthetic": synthetic,
        "equivalence": equivalence,
        "cards": lambda: (build_cards(ROOT) and 0),
        "validate": validate,
    }
    if args.command == "all":
        for action in (synthetic, equivalence, lambda: (build_cards(ROOT) and 0), validate):
            if action():
                return 1
        return 0
    return actions[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())

