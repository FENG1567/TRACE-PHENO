"""Generate small, machine-readable cards from public configurations."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def build_cards(root: Path) -> list[Path]:
    output = root / "results" / "cards"
    output.mkdir(parents=True, exist_ok=True)
    with (root / "configs" / "phenotype_definitions.csv").open(encoding="utf-8-sig", newline="") as handle:
        definitions = list(csv.DictReader(handle))
    cards = []
    for row in definitions:
        card = {
            "card_type": "phenotype",
            "phenotype": row["phenotype"],
            "version": row["version"],
            "target_construct": "acute pancreatitis",
            "reference_type": "Blinded two-clinician-adjudicated reference set; exploratory conditional agreement only",
            "definition": row["definition"],
            "intended_use": row["intended_use"],
            "not_for": row["not_for"],
            "known_limitations": row["limitations"],
        }
        path = output / f"{row['phenotype']}_card.json"
        path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        cards.append(path)
    return cards

