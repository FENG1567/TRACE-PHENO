"""Small, exhaustive rule-equivalence checker for transparent Boolean rules."""

from __future__ import annotations

import hashlib
import itertools
import json


def atlanta_like(pain: bool, enzyme: bool, imaging: bool) -> bool:
    return sum((pain, enzyme, imaging)) >= 2


def transparent_score(pain: bool, enzyme: bool, imaging: bool) -> bool:
    return 0.35 * pain + 0.35 * enzyme + 0.30 * imaging >= 0.40


def p3_p4_equivalence() -> dict[str, object]:
    truth_table = []
    for pain, enzyme, imaging in itertools.product((False, True), repeat=3):
        p3 = atlanta_like(pain, enzyme, imaging)
        p4 = transparent_score(pain, enzyme, imaging)
        truth_table.append({"pain": pain, "enzyme": enzyme, "imaging": imaging, "P3": p3, "P4": p4})
    equivalent = all(row["P3"] == row["P4"] for row in truth_table)
    canonical = json.dumps(truth_table, sort_keys=True, separators=(",", ":"))
    return {
        "equivalent": equivalent,
        "scope": "complete binary three-domain inputs under frozen weights and threshold",
        "truth_table": truth_table,
        "canonical_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }

