"""Check the non-identifying cohort summary against two disjoint P0 partitions."""
import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def counts(n, percentage):
    """Integer counts consistent with a percentage preserved to two decimals."""
    target = Decimal(percentage).quantize(Decimal("0.01"))
    return [k for k in range(n + 1)
            if (Decimal(100 * k) / Decimal(n)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN) == target]


def check(data):
    burden = {r["phenotype"]: r for r in read(data / "Figure_5_Burden.csv")}
    decomposition = read(data / "Figure_5_Set_Decomposition.csv")
    p0 = burden["P0"]
    summaries = []
    for comparison, only in [("P0 vs P1", "P0-only secondary-position"),
                             ("P0 vs P3", "P0-only")]:
        rows = [r for r in decomposition
                if r["comparison"] == comparison
                and r["set_component"] in ("both/P1", "both", only)]
        if len(rows) != 2 or sum(int(r["n"]) for r in rows) != int(p0["admissions"]):
            raise ValueError(f"{comparison}: P0 partition denominator mismatch")
        possible = {0}
        for row in rows:
            possible = {a + b for a in possible
                        for b in counts(int(row["n"]), row["icu_pct"])}
        if len(possible) != 1:
            raise ValueError(f"{comparison}: ICU numerator is not uniquely recoverable")
        count = possible.pop()
        expected = (Decimal(100 * count) / Decimal(p0["admissions"])).quantize(Decimal("0.1"))
        if Decimal(p0["icu_pct"]) != expected:
            raise ValueError(f"P0 ICU summary {p0['icu_pct']}% differs from {count}/{p0['admissions']} ({expected}%)")
        summaries.append({"partition": comparison, "icu_admissions": count,
                          "admissions": int(p0["admissions"]), "icu_percent": str(expected)})
    if len({r["icu_admissions"] for r in summaries}) != 1:
        raise ValueError("P0 partitions imply different ICU numerators")
    return {"status": "PASS", "partitions": summaries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "figures" / "PublicationLayout" / "source_data" / "frozen")
    print(json.dumps(check(parser.parse_args().data_dir), indent=2))
