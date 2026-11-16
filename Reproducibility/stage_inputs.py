"""Create minimal identifier-free inputs for the restricted reanalysis."""
from __future__ import annotations

import argparse
import csv
import os
import hashlib
import json
import secrets
from collections import Counter, defaultdict
from pathlib import Path


PROJECT = None
OUT = Path(__file__).resolve().parent / "inputs"
SEED_REFERENCE = 20260816
SEED_DOWNSTREAM = 20260815


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def truth(value: str | None) -> bool:
    return value == "True"


REFERENCE_LABEL_COLUMNS = {"review_case_id", "variant", "final_label"}


def validate_reference_label_file(path: Path, ref_dir: Path) -> Path:
    """Validate the selected label table's location, format, and required header."""
    if not path.is_file():
        raise FileNotFoundError(f"reference label file does not exist or is not a file: {path}")
    try:
        path.relative_to(ref_dir)
    except ValueError as exc:
        raise ValueError(f"reference label file must be inside {ref_dir}: {path}") from exc
    if path.suffix.lower() != ".csv":
        raise ValueError(f"reference label file must be a .csv file: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle), None)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"cannot read reference label CSV {path}: {exc}") from exc
    if not header:
        raise ValueError(f"reference label CSV is empty or has no header: {path}")
    if len(header) != len(set(header)):
        raise ValueError(f"reference label CSV has duplicate column names: {path}")
    missing = sorted(REFERENCE_LABEL_COLUMNS.difference(header))
    if missing:
        raise ValueError(f"reference label CSV is missing required columns {missing}: {path}")
    return path


def resolve_reference_labels(ref_dir: Path, requested_path: str | Path | None = None) -> Path:
    """Resolve a sole candidate by default, or validate an explicit selection.

    Relative explicit paths are interpreted under ``ref_dir``. The canonical
    filename has no priority when other candidate label tables are present.
    """
    ref_dir = ref_dir.expanduser().resolve()
    if requested_path is not None:
        supplied = Path(requested_path).expanduser()
        candidate = supplied if supplied.is_absolute() else ref_dir / supplied
        try:
            candidate = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"--reference-label-file does not exist: {candidate}") from exc
        return validate_reference_label_file(candidate, ref_dir)

    candidates = sorted(
        p.resolve()
        for p in ref_dir.glob("*REFERENCE*SET*.csv")
        if p.is_file()
    )
    if len(candidates) == 1:
        return validate_reference_label_file(candidates[0], ref_dir)
    if not candidates:
        raise FileNotFoundError(
            f"no reference label CSV matching '*REFERENCE*SET*.csv' found in {ref_dir}; "
            "supply --reference-label-file with the intended CSV filename"
        )
    names = "\n".join(f"  - {p.name}" for p in candidates)
    raise ValueError(
        f"ambiguous reference label CSVs in {ref_dir}:\n{names}\n"
        "select the intended table with --reference-label-file <filename> "
        f"(a relative path is resolved under {ref_dir})"
    )


def make_reference_inputs(labels_path: Path) -> dict[str, dict[str, object]]:
    ref_dir = PROJECT / "03_reference_standard"
    split_path = ref_dir / "DEV_VALIDATION_SPLIT.csv"
    packet_path = ref_dir / "PACKET_MANIFEST.csv"
    design_path = ref_dir / "SAMPLING_WEIGHTS.json"

    strict_labels = {
        row["review_case_id"]: row["final_label"]
        for row in read_csv(labels_path)
        if row["variant"] == "strict"
    }
    packet_case = {row["hadm_id"]: row["review_case_id"] for row in read_csv(packet_path)}
    split_rows = read_csv(split_path)
    val = [row for row in split_rows if row["split"] == "val"]
    if not val or len({row["hadm_id"] for row in val}) != len(val):
        raise ValueError("Validation sample is empty or has duplicate admissions")
    if any(not truth(row["representative"]) for row in val):
        raise ValueError("Validation rows do not all use the representative-patient unit")
    if len({row["subject_id"] for row in val}) != len(val):
        raise ValueError("Validation split contains repeated patients")

    design = json.loads(design_path.read_text(encoding="utf-8"))
    pools = {key: int(value) for key, value in design["patient_pools"].items()}
    val_by_stratum = Counter(row["pat_stratum"] for row in val)
    if set(val_by_stratum) != set(pools):
        raise ValueError("Validation strata do not match the frozen patient pools")

    staged: list[dict[str, object]] = []
    label_counts = Counter()
    for row in val:
        case_id = packet_case.get(row["hadm_id"])
        if case_id is None or case_id not in strict_labels:
            raise ValueError("A validation admission has no strict reference label")
        label = strict_labels[case_id]
        label_counts[label] += 1
        staged.append(
            {
                "stratum": row["pat_stratum"],
                "final_label": label,
                "weight": pools[row["pat_stratum"]] / val_by_stratum[row["pat_stratum"]],
                "P0": truth(row["icd_ap_any"]),
                "P1": truth(row["icd_ap_primary"]),
                "enzyme_ge3": truth(row["enz_full_ge3"]),
                "has_enzyme": truth(row["enz_any"]),
                "pain_pos": truth(row["text_pain_pos"]),
                "pain_neg": truth(row["text_pain_neg"]),
                "image_pos": truth(row["img_pos"]),
                "image_neg": truth(row["img_neg"]),
            }
        )

    strict_n = label_counts["definitive_AP"] + label_counts["non_AP"]
    probable_pos_n = strict_n + label_counts["probable_AP"]
    probable_neg_n = probable_pos_n
    if (strict_n, label_counts["definitive_AP"], label_counts["non_AP"]) != (86, 20, 66):
        raise ValueError(f"Strict validation counts mismatch: {label_counts}")
    if probable_pos_n != 143 or probable_neg_n != 143:
        raise ValueError(f"Boundary-policy validation counts mismatch: {label_counts}")

    write_csv(
        OUT / "validation_inputs.csv",
        staged,
        [
            "stratum", "final_label", "weight", "P0", "P1", "enzyme_ge3", "has_enzyme",
            "pain_pos", "pain_neg", "image_pos", "image_neg",
        ],
    )
    design_rows = []
    formal_counts = Counter(row["pat_stratum"] for row in split_rows)
    dev_counts = Counter(row["pat_stratum"] for row in split_rows if row["split"] == "dev")
    for stratum in sorted(pools):
        design_rows.append(
            {
                "stratum": stratum,
                "patient_pool_N": pools[stratum],
                "formal_sample_n": formal_counts[stratum],
                "development_n": dev_counts[stratum],
                "validation_n": val_by_stratum[stratum],
            }
        )
    write_csv(
        OUT / "sampling_design_inputs.csv",
        design_rows,
        ["stratum", "patient_pool_N", "formal_sample_n", "development_n", "validation_n"],
    )
    label_source_path = labels_path.relative_to(PROJECT).as_posix()
    return {
        "validation_inputs.csv": {"rows": len(staged), "sha256": sha256(OUT / "validation_inputs.csv")},
        "sampling_design_inputs.csv": {"rows": len(design_rows), "sha256": sha256(OUT / "sampling_design_inputs.csv")},
        "counts": {
            "strict_n": strict_n,
            "strict_positive_n": label_counts["definitive_AP"],
            "strict_negative_n": label_counts["non_AP"],
            "probable_positive_policy_n": probable_pos_n,
            "probable_positive_n": label_counts["definitive_AP"] + label_counts["probable_AP"],
            "probable_negative_policy_n": probable_neg_n,
            "probable_negative_n": label_counts["definitive_AP"],
            "label_counts_in_validation": dict(label_counts),
        },
        "source_hashes": {p.name: sha256(p) for p in (split_path, labels_path, packet_path, design_path)},
        "reference_label_source": {
            "filename": labels_path.name,
            "path": label_source_path,
            "sha256": sha256(labels_path),
        },
        "source_relative_paths": [
            "03_reference_standard/DEV_VALIDATION_SPLIT.csv",
            label_source_path,
            "03_reference_standard/PACKET_MANIFEST.csv",
            "03_reference_standard/SAMPLING_WEIGHTS.json",
        ],
    }


def make_downstream_input() -> dict[str, object]:
    frame_path = PROJECT / "03_reference_standard" / "CANDIDATE_FRAME.csv"
    values = ("P0", "P1", "P2", "P3")
    patient_summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {f"n_{p}": 0 for p in values} | {f"d_{p}": 0 for p in values}
    )
    totals = {p: {"n": 0, "deaths": 0} for p in values}
    total_rows = 0

    with frame_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total_rows += 1
            subject = row["subject_id"]
            death = bool(row.get("deathtime"))
            icd_any = truth(row.get("icd_ap_any"))
            icd_primary = truth(row.get("icd_ap_primary"))
            enzyme_ge3 = truth(row.get("enz_full_ge3"))
            has_enzyme = truth(row.get("enz_any"))
            pain = truth(row.get("text_pain_pos")) and not truth(row.get("text_pain_neg"))
            image = truth(row.get("img_pos"))
            memberships = {
                "P0": icd_any,
                "P1": icd_primary,
                "P2": icd_any and has_enzyme and enzyme_ge3,
                "P3": int(pain) + int(enzyme_ge3) + int(image) >= 2,
            }
            if any(memberships.values()):
                patient = patient_summary[subject]
                for phenotype, member in memberships.items():
                    if member:
                        patient[f"n_{phenotype}"] += 1
                        patient[f"d_{phenotype}"] += int(death)
                        totals[phenotype]["n"] += 1
                        totals[phenotype]["deaths"] += int(death)

    expected = {
        "P0": {"n": 3266, "deaths": 123},
        "P1": {"n": 1825, "deaths": 15},
        "P2": {"n": 887, "deaths": 39},
        "P3": {"n": 22725, "deaths": 819},
    }
    if total_rows != 546028:
        raise ValueError(f"Candidate frame row count mismatch: {total_rows}")
    if totals != expected:
        raise ValueError(f"Candidate-frame phenotype/death counts do not match frozen aggregate: {totals}")

    # Random group tokens have no mapping to source patient IDs in the payload.
    output_rows: list[dict[str, object]] = []
    # Preserve the original sorted-subject resampling order without sending IDs.
    ordered_patients = sorted(patient_summary)
    tokens = [secrets.token_hex(12) for _ in ordered_patients]
    for token, subject in zip(tokens, ordered_patients):
        summary = patient_summary[subject]
        output_rows.append({"cluster_token": token, **summary})
    fields = ["cluster_token"] + [f"{x}_{p}" for p in values for x in ("n", "d")]
    write_csv(OUT / "mimic_patient_cluster_counts.csv", output_rows, fields)
    return {
        "mimic_patient_cluster_counts.csv": {
            "rows": len(output_rows),
            "sha256": sha256(OUT / "mimic_patient_cluster_counts.csv"),
            "columns": fields,
            "contains_original_patient_or_admission_ids": False,
        },
        "source_hash": sha256(frame_path),
        "source_relative_path": "03_reference_standard/CANDIDATE_FRAME.csv",
        "source_rows": total_rows,
        "phenotype_death_totals": totals,
        "random_cluster_tokens": True,
    }


def make_aggregate_inputs() -> dict[str, object]:
    root = PROJECT
    eicu = json.loads((root / "05_transport" / "EICU_TRANSPORT_REPORT.json").read_text(encoding="utf-8"))
    nwicu = json.loads((root / "05_transport" / "NWICU_TRANSPORT_REPORT.json").read_text(encoding="utf-8"))
    sic_hirid = json.loads((root / "05_transport" / "SICDB_AND_HIRID_REPORT.json").read_text(encoding="utf-8"))
    downstream = json.loads((root / "06_downstream" / "MIMIC_DOWNSTREAM.json").read_text(encoding="utf-8"))
    eicu_downstream = json.loads((root / "06_downstream" / "EICU_NWICU_SICDB_DOWNSTREAM.json").read_text(encoding="utf-8"))
    risk = json.loads((root / "06_downstream" / "MIMIC_RISK_MODEL.json").read_text(encoding="utf-8"))

    safe = {
        "transport": {
            "MIMIC": {
                "base_n": downstream["base_cohort"]["n_admissions"],
                "yield": {k: downstream["membership"][k] for k in ("P0", "P1", "P2", "P3")},
                "deaths": {"P0": 123, "P1": 15, "P2": 39, "P3": 819},
            },
            "eICU": {
                "base_n": eicu_downstream["eICU"]["base_stays"],
                "P0": eicu["code_system"]["ap_stays_any"],
                "P1": eicu["code_system"]["primary_major"],
                "P2_proxy": eicu["proxy_uln"]["P2_proxy_yield"],
                "P2_direct_status": "not_computable",
                "P3_status": "not_computable",
                "P4_status": "not_computable",
                "P0_P2_decomposition": eicu_downstream["eICU"]["decomposition"]["P0_vs_P2"],
            },
            "NWICU": {
                "base_n": nwicu["n_admissions"],
                "P0": nwicu["P0_any_icd"]["yield"],
                "P1": nwicu["P1_primary_icd"]["yield"],
                "P2": nwicu["P2_icd_plus_enzyme"]["yield"],
                "P3_status": nwicu["P3"]["status"],
                "P4_status": nwicu["P4_P5"]["status"],
                "P2_definition": "ap_any intersection enz_ge3, per code/audit source",
            },
            "SICdb": {
                "base_n": sic_hirid["SICdb"]["n_cases"],
                "P0": sic_hirid["SICdb"]["P0"]["yield"],
                "P0_status": sic_hirid["SICdb"]["P0"]["status"],
                "P1": sic_hirid["SICdb"]["P1"]["yield"],
                "P1_status": sic_hirid["SICdb"]["P1"]["status"],
                "P2_status": sic_hirid["SICdb"]["P2"]["status"],
                "P3_P4_status": sic_hirid["SICdb"]["P3_P4_P5"]["status"],
            },
            "HiRID": {
                "base_n": sic_hirid["HiRID"]["n_patients"],
                "P0_P1_P2_status": sic_hirid["HiRID"]["P0_P1_P2"],
                "P3_status": sic_hirid["HiRID"]["P3"],
                "P4_P5_status": sic_hirid["HiRID"]["P4_P5"],
            },
        },
        "downstream_prior": {
            "base_n": downstream["base_cohort"]["n_admissions"],
            "P0_n": downstream["membership"]["P0"],
            "P0_deaths": 123,
            "P1_n": downstream["membership"]["P1"],
            "P1_deaths": 15,
        },
    }
    path = OUT / "aggregate_context_inputs.json"
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    sources = [
        root / "05_transport" / "EICU_TRANSPORT_REPORT.json",
        root / "05_transport" / "NWICU_TRANSPORT_REPORT.json",
        root / "05_transport" / "SICDB_AND_HIRID_REPORT.json",
        root / "06_downstream" / "MIMIC_DOWNSTREAM.json",
        root / "06_downstream" / "EICU_NWICU_SICDB_DOWNSTREAM.json",
        root / "06_downstream" / "MIMIC_RISK_MODEL.json",
        root / "code" / "audit" / "eicu_downstream.py",
        root / "code" / "audit" / "nwicu_transport.py",
        root / "code" / "audit" / "mimic_risk_model.py",
    ]
    return {
        path.name: {"sha256": sha256(path), "bytes": path.stat().st_size},
        "source_hashes": {p.relative_to(root).as_posix(): sha256(p) for p in sources},
    }


def main() -> None:
    global PROJECT
    parser = argparse.ArgumentParser(description="Create identifier-free inputs in an authorized source environment.")
    parser.add_argument("--project-root", default=os.environ.get("TRACE_PHENO_PROJECT_ROOT"),
                        help="Path to the authorized trace_pheno project (or set TRACE_PHENO_PROJECT_ROOT).")
    parser.add_argument(
        "--reference-label-file",
        help=(
            "Exact reference-label CSV to use; relative paths are resolved under "
            "<project-root>/03_reference_standard. Required when multiple candidates exist."
        ),
    )
    args = parser.parse_args()
    if not args.project_root:
        parser.error("supply --project-root or set TRACE_PHENO_PROJECT_ROOT")
    PROJECT = Path(args.project_root).expanduser().resolve()
    required = [PROJECT / "03_reference_standard", PROJECT / "05_transport", PROJECT / "06_downstream"]
    if not all(path.is_dir() for path in required):
        parser.error("project root must contain 03_reference_standard, 05_transport, and 06_downstream")
    try:
        labels_path = resolve_reference_labels(PROJECT / "03_reference_standard", args.reference_label_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "purpose": "Minimal aggregate and de-identified inputs for restricted reproducible analyses",
        "reference_seed": SEED_REFERENCE,
        "reference_bootstrap_replicates": 5000,
        "downstream_seed": SEED_DOWNSTREAM,
        "downstream_bootstrap_replicates": 2000,
        "reference": make_reference_inputs(labels_path),
        "downstream": make_downstream_input(),
        "aggregate": make_aggregate_inputs(),
    }
    (OUT / "input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
