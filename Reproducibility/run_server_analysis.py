"""Run the aggregate-only TRACE-PHENO revision analyses in the restricted environment."""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs"
OUTPUT = ROOT / "outputs"
REF_SEED = 20260816
REF_BOOT = 5000
DOWNSTREAM_SEED = 20260815
DOWNSTREAM_BOOT = 2000
STRATA = ["S1_A1", "S1_A2", "S2", "S3", "S4"]
POLICIES = {
    "strict": {"definitive_AP": 1, "non_AP": 0},
    "probable_positive": {"definitive_AP": 1, "probable_AP": 1, "non_AP": 0},
    "probable_negative": {"definitive_AP": 1, "probable_AP": 0, "non_AP": 0},
    "all_uncertain_positive": {
        "definitive_AP": 1,
        "probable_AP": 1,
        "indeterminate": 1,
        "non_AP": 0,
    },
    "all_uncertain_negative": {
        "definitive_AP": 1,
        "probable_AP": 0,
        "indeterminate": 0,
        "non_AP": 0,
    },
}
PHENOTYPES = ("P0", "P1", "P2", "P3")
CLINICAL_PHENOTYPES = ("P0", "P1", "P2")
METRICS = ("sensitivity", "specificity", "ppv", "npv")
CLINICAL_REFERENCE_STATUS = "Clinician-adjudicated reference (two independent clinicians; third adjudicator)"
P3_REFERENCE_STATUS = "Clinician-adjudicated reference (two independent clinicians; third adjudicator); P3 shares evidence rules and is rule concordance, not independent clinical validation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def reference_label_source_from_manifest(manifest_path: Path | None = None) -> dict[str, str]:
    """Read and validate the selected reference-label source recorded at staging."""
    path = manifest_path or INPUT / "input_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}; restage inputs with stage_inputs.py so the selected "
            "reference-label filename, path, and SHA-256 are recorded"
        )
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read staged input manifest {path}: {exc}") from exc
    reference = manifest.get("reference") if isinstance(manifest, dict) else None
    source = reference.get("reference_label_source") if isinstance(reference, dict) else None
    if not isinstance(source, dict):
        raise ValueError(
            f"{path} does not record reference.reference_label_source; restage inputs "
            "with the updated stage_inputs.py before running the analysis"
        )

    filename = source.get("filename")
    source_path = source.get("path")
    digest = source.get("sha256")
    if not all(isinstance(value, str) and value for value in (filename, source_path, digest)):
        raise ValueError(f"invalid reference_label_source fields in {path}")
    relative_path = PurePosixPath(source_path)
    if relative_path.is_absolute() or ".." in relative_path.parts or relative_path.name != filename:
        raise ValueError(f"invalid reference-label source path in {path}: {source_path}")
    if len(digest) != 64 or any(character not in "0123456789abcdefABCDEF" for character in digest):
        raise ValueError(f"invalid SHA-256 for reference-label source in {path}")
    source_hashes = reference.get("source_hashes")
    if not isinstance(source_hashes, dict) or source_hashes.get(filename) != digest:
        raise ValueError(f"reference-label source SHA-256 does not match source_hashes in {path}")
    for staged_name in ("validation_inputs.csv", "sampling_design_inputs.csv"):
        staged_metadata = reference.get(staged_name)
        staged_digest = staged_metadata.get("sha256") if isinstance(staged_metadata, dict) else None
        if not isinstance(staged_digest, str) or len(staged_digest) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in staged_digest
        ):
            raise ValueError(f"missing or invalid SHA-256 for {staged_name} in {path}; restage inputs")
        staged_path = path.parent / staged_name
        if not staged_path.is_file():
            raise FileNotFoundError(
                f"missing staged reference input {staged_path}; restage inputs before analysis"
            )
        if sha256(staged_path) != staged_digest.lower():
            raise ValueError(
                f"staged {staged_name} SHA-256 does not match {path}; the manifest may be stale "
                "after a partial restage. Restage inputs before analysis"
            )
    return {"filename": filename, "path": source_path, "sha256": digest.lower()}


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: str) -> bool:
    return value.lower() == "true"


def prepare_reference() -> tuple[list[dict[str, object]], dict[str, int]]:
    raw = read_csv(INPUT / "validation_inputs.csv")
    design = read_csv(INPUT / "sampling_design_inputs.csv")
    weights = {r["stratum"]: int(r["patient_pool_N"]) for r in design}
    val_n = Counter(r["stratum"] for r in raw)
    rows: list[dict[str, object]] = []
    for r in raw:
        if r["stratum"] not in weights or val_n[r["stratum"]] < 1:
            raise ValueError("Invalid validation stratum")
        expected_weight = weights[r["stratum"]] / val_n[r["stratum"]]
        if not np.isclose(float(r["weight"]), expected_weight, rtol=0, atol=1e-10):
            raise ValueError("Input design weight does not equal patient pool / validation n")
        row: dict[str, object] = {
            "stratum": r["stratum"],
            "final_label": r["final_label"],
            "weight": float(r["weight"]),
            "P0": as_bool(r["P0"]),
            "P1": as_bool(r["P1"]),
        }
        enzyme = as_bool(r["enzyme_ge3"])
        row["P2"] = row["P0"] and as_bool(r["has_enzyme"]) and enzyme
        pain = as_bool(r["pain_pos"]) and not as_bool(r["pain_neg"])
        image = as_bool(r["image_pos"])
        row["P3"] = int(pain) + int(enzyme) + int(image) >= 2
        rows.append(row)

    label_counts = Counter(row["final_label"] for row in rows)
    strict = label_counts["definitive_AP"] + label_counts["non_AP"]
    pp = strict + label_counts["probable_AP"]
    if (len(rows), strict, label_counts["definitive_AP"], label_counts["non_AP"], pp) != (240, 86, 20, 66, 143):
        raise ValueError(f"Validation label counts failed frozen checks: {label_counts}")
    if len({row["stratum"] for row in rows}) != 5:
        raise ValueError("Expected five reference-sample strata")
    return rows, dict(val_n)


def label(row: dict[str, object], mapping: dict[str, int]) -> int | None:
    value = mapping.get(str(row["final_label"]))
    return value


def components(rows: list[dict[str, object]], phenotype: str, mapping: dict[str, int], weighted: bool) -> dict[str, float]:
    counts = {key: 0.0 for key in ("tp", "fp", "fn", "tn")}
    for row in rows:
        y = label(row, mapping)
        if y is None:
            continue
        predicted = bool(row[phenotype])
        weight = float(row["weight"]) if weighted else 1.0
        key = "tp" if predicted and y else "fp" if predicted else "fn" if y else "tn"
        counts[key] += weight
    return counts


def metric_values(c: dict[str, float]) -> dict[str, float | None]:
    def ratio(a: float, b: float) -> float | None:
        return a / (a + b) if a + b > 0 else None

    return {
        "sensitivity": ratio(c["tp"], c["fn"]),
        "specificity": ratio(c["tn"], c["fp"]),
        "ppv": ratio(c["tp"], c["fp"]),
        "npv": ratio(c["tn"], c["fn"]),
    }


def _agreement(rows: list[dict[str, object]], policy: dict[str, int], weighted: bool) -> float | None:
    denominator = numerator = 0.0
    for row in rows:
        y = label(row, policy)
        if y is None:
            continue
        weight = float(row["weight"]) if weighted else 1.0
        denominator += weight
        numerator += weight * (int(bool(row["P3"])) == y)
    return numerator / denominator if denominator else None


def bootstrap_reference(
    rows: list[dict[str, object]], policy: dict[str, int], phenotype: str, rng: np.random.Generator
) -> tuple[
    dict[str, tuple[float | None, float | None]],
    dict[str, tuple[float | None, float | None]],
    tuple[float | None, float | None],
    tuple[float | None, float | None],
]:
    by_stratum: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_stratum[str(row["stratum"])].append(row)
    weighted_draws: dict[str, list[float]] = defaultdict(list)
    unweighted_draws: dict[str, list[float]] = defaultdict(list)
    agreement_draws: dict[str, list[float]] = {"weighted": [], "unweighted": []}
    for _ in range(REF_BOOT):
        sample: list[dict[str, object]] = []
        for stratum in STRATA:
            pool = by_stratum[stratum]
            picks = rng.integers(0, len(pool), size=len(pool))
            sample.extend(pool[int(i)] for i in picks)
        for weighted, store in ((True, weighted_draws), (False, unweighted_draws)):
            values = metric_values(components(sample, phenotype, policy, weighted))
            for name, value in values.items():
                if value is not None:
                    store[name].append(value)
        if phenotype == "P3":
            for weighted, scale in ((True, "weighted"), (False, "unweighted")):
                agreement_value = _agreement(sample, policy, weighted)
                if agreement_value is not None:
                    agreement_draws[scale].append(agreement_value)

    def intervals(draws: dict[str, list[float]]) -> dict[str, tuple[float | None, float | None]]:
        output = {}
        for name in METRICS:
            values = draws.get(name, [])
            output[name] = (float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))) if values else (None, None)
        return output

    def agreement_interval(values: list[float]) -> tuple[float | None, float | None]:
        return (float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))) if values else (None, None)

    return (
        intervals(weighted_draws),
        intervals(unweighted_draws),
        agreement_interval(agreement_draws["weighted"]),
        agreement_interval(agreement_draws["unweighted"]),
    )


def kish_wilson(successes: float, total: float, total_w2: float, z: float = 1.959963984540054) -> tuple[float, float, float]:
    if total <= 0 or total_w2 <= 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / total
    n_eff = total * total / total_w2
    z2 = z * z
    den = 1.0 + z2 / n_eff
    center = (p + z2 / (2 * n_eff)) / den
    half = z * np.sqrt(p * (1 - p) / n_eff + z2 / (4 * n_eff * n_eff)) / den
    lower = 0.0 if p == 0 else float(max(0, center - half))
    upper = 1.0 if p == 1 else float(min(1, center + half))
    return lower, upper, float(n_eff)


def clopper_pearson(successes: int, total: int, alpha: float = 0.05) -> tuple[float, float]:
    if total <= 0:
        return (float("nan"), float("nan"))
    low = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, total - successes + 1))
    high = 1.0 if successes == total else float(beta.ppf(1 - alpha / 2, successes + 1, total - successes))
    return low, high


def boundary_ci_rows(rows: list[dict[str, object]], policy_name: str, mapping: dict[str, int]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for phenotype in CLINICAL_PHENOTYPES:
        for metric in METRICS:
            weighted_num = weighted_den = weighted_den2 = 0.0
            unweighted_success = unweighted_n = 0
            for row in rows:
                y = label(row, mapping)
                if y is None:
                    continue
                pred = bool(row[phenotype])
                eligible = (
                    y == 1 if metric == "sensitivity" else
                    y == 0 if metric == "specificity" else
                    pred if metric == "ppv" else not pred
                )
                if not eligible:
                    continue
                if metric == "sensitivity":
                    success = pred
                elif metric == "specificity":
                    success = not pred
                elif metric == "ppv":
                    success = y == 1
                else:
                    success = y == 0
                w = float(row["weight"])
                weighted_den += w
                weighted_den2 += w * w
                weighted_num += w * int(success)
                unweighted_n += 1
                unweighted_success += int(success)
            low, high, n_eff = kish_wilson(weighted_num, weighted_den, weighted_den2)
            u_low, u_high = clopper_pearson(unweighted_success, unweighted_n)
            result.extend(
                [
                    {
                        "policy": policy_name,
                        "phenotype": phenotype,
                        "metric": metric,
                        "scale": "design_weighted",
                        "estimate": weighted_num / weighted_den if weighted_den else None,
                        "ci_lower": low,
                        "ci_upper": high,
                        "denominator_n": unweighted_n,
                        "effective_n_kish": n_eff,
                        "ci_method": "Kish effective-n Wilson score interval",
                    },
                    {
                        "policy": policy_name,
                        "phenotype": phenotype,
                        "metric": metric,
                        "scale": "unweighted_sample",
                        "estimate": unweighted_success / unweighted_n if unweighted_n else None,
                        "ci_lower": u_low,
                        "ci_upper": u_high,
                        "denominator_n": unweighted_n,
                        "effective_n_kish": None,
                        "ci_method": "Clopper-Pearson exact interval",
                    },
                ]
            )
    return result


def run_reference() -> dict[str, object]:
    rows, val_n = prepare_reference()
    rng = np.random.default_rng(REF_SEED)
    metric_rows: list[dict[str, object]] = []
    confusion_rows: list[dict[str, object]] = []
    rule_rows: list[dict[str, object]] = []
    boundary_rows: list[dict[str, object]] = []
    policy_counts: list[dict[str, object]] = []

    for policy_name, mapping in POLICIES.items():
        eligible = [r for r in rows if label(r, mapping) is not None]
        positives = sum(label(r, mapping) == 1 for r in eligible)
        negatives = len(eligible) - positives
        policy_counts.append(
            {"policy": policy_name, "eligible_n": len(eligible), "positive_n": positives, "negative_n": negatives}
        )
        for phenotype in PHENOTYPES:
            wc = components(rows, phenotype, mapping, True)
            uc = components(rows, phenotype, mapping, False)
            weighted_values = metric_values(wc)
            unweighted_values = metric_values(uc)
            weighted_ci, unweighted_ci, weighted_agreement_ci, unweighted_agreement_ci = bootstrap_reference(rows, mapping, phenotype, rng)
            for scale, comp in (("design_weighted", wc), ("unweighted_sample", uc)):
                if phenotype in CLINICAL_PHENOTYPES:
                    confusion_rows.append(
                        {
                            "policy": policy_name,
                            "phenotype": phenotype,
                            "scale": scale,
                            "eligible_n": len(eligible),
                            "positive_n": positives,
                            "negative_n": negatives,
                            **comp,
                        }
                    )
            for scale, values, cis in (
                ("design_weighted", weighted_values, weighted_ci),
                ("unweighted_sample", unweighted_values, unweighted_ci),
            ):
                for metric in METRICS:
                    if phenotype in CLINICAL_PHENOTYPES:
                        metric_rows.append(
                            {
                                "policy": policy_name,
                                "phenotype": phenotype,
                                "scale": scale,
                                "metric": metric,
                                "estimate": values[metric],
                                "ci_lower": cis[metric][0],
                                "ci_upper": cis[metric][1],
                                "bootstrap_ci_lower": cis[metric][0],
                                "bootstrap_ci_upper": cis[metric][1],
                                "ci_level": 0.95,
                                "ci_method": f"{REF_BOOT}-replicate stratified patient bootstrap",
                                "ci_method_bootstrap": f"{REF_BOOT}-replicate stratified patient bootstrap",
                                "degenerate_boundary": False,
                                "eligible_n": len(eligible),
                                "positive_n": positives,
                                "negative_n": negatives,
                                "target_frame": "patient frame; one prespecified representative hospitalization per patient",
                                "reference_status": CLINICAL_REFERENCE_STATUS,
                            }
                        )
            if phenotype == "P3":
                for weighted, scale in ((True, "design_weighted"), (False, "unweighted_sample")):
                    agreement = _agreement(rows, mapping, weighted)
                    total = sum((float(r["weight"]) if weighted else 1.0) for r in eligible)
                    matches = agreement * total if agreement is not None else None
                    if weighted:
                        total_w2 = sum(float(r["weight"]) ** 2 for r in eligible)
                        robust_low, robust_high, effective_n = kish_wilson(float(matches or 0), total, total_w2)
                        raw_low, raw_high = weighted_agreement_ci
                    else:
                        match_n = sum(bool(r["P3"]) == label(r, mapping) for r in eligible)
                        robust_low, robust_high = clopper_pearson(match_n, len(eligible))
                        effective_n = None
                        raw_low, raw_high = unweighted_agreement_ci
                    degenerate_boundary = (
                        agreement in (0.0, 1.0)
                        and raw_low is not None
                        and raw_high == raw_low
                    )
                    if degenerate_boundary:
                        ci_low, ci_high = robust_low, robust_high
                        ci_method = "Kish effective-n Wilson score interval for a degenerate boundary interval" if weighted else "Clopper-Pearson exact interval for a degenerate boundary interval"
                    else:
                        ci_low, ci_high = raw_low, raw_high
                        ci_method = f"{REF_BOOT}-replicate stratified patient bootstrap" if raw_low is not None else "not estimated"
                    rule_rows.append(
                        {
                            "policy": policy_name,
                            "scale": scale,
                            "eligible_n": len(eligible),
                            "positive_n": positives,
                            "negative_n": negatives,
                            "weighted_or_sample_matches": matches,
                            "weighted_or_sample_eligible_total": total,
                            "rule_concordance": agreement,
                            "ci_lower": ci_low,
                            "ci_upper": ci_high,
                            "effective_n_kish": effective_n,
                            "bootstrap_ci_lower": raw_low,
                            "bootstrap_ci_upper": raw_high,
                            "ci_method": ci_method,
                            "ci_method_bootstrap": f"{REF_BOOT}-replicate stratified patient bootstrap" if raw_low is not None else "not estimated",
                            "degenerate_boundary": degenerate_boundary,
                            "reference_status": P3_REFERENCE_STATUS,
                        }
                    )
        boundary_rows.extend(boundary_ci_rows(rows, policy_name, mapping))

    # Replace only zero-width bootstrap intervals at an exact boundary. Keep the
    # raw bootstrap bounds and method alongside the boundary-interval values.
    boundary_index = {
        (str(row["policy"]), str(row["phenotype"]), str(row["metric"]), str(row["scale"])): row
        for row in boundary_rows
    }
    for row in metric_rows:
        low = row["bootstrap_ci_lower"]
        high = row["bootstrap_ci_upper"]
        estimate = row["estimate"]
        if estimate in (0, 1) and low == high == estimate:
            boundary_row = boundary_index[(str(row["policy"]), str(row["phenotype"]), str(row["metric"]), str(row["scale"]))]
            row["ci_lower"] = boundary_row["ci_lower"]
            row["ci_upper"] = boundary_row["ci_upper"]
            row["ci_method"] = f"{boundary_row['ci_method']} for a degenerate boundary interval"
            row["degenerate_boundary"] = True

    write_csv(OUTPUT / "BENCHMARK_METRICS.csv", metric_rows, list(metric_rows[0]))
    write_csv(OUTPUT / "BENCHMARK_CONFUSION.csv", confusion_rows, list(confusion_rows[0]))
    write_csv(OUTPUT / "VALIDATION_POLICY_COUNTS.csv", policy_counts, list(policy_counts[0]))
    write_csv(OUTPUT / "P3_RULE_CONCORDANCE.csv", rule_rows, list(rule_rows[0]))
    write_csv(OUTPUT / "BOUNDARY_INTERVALS.csv", boundary_rows, list(boundary_rows[0]))

    sampling_rows: list[dict[str, object]] = []
    for source in read_csv(INPUT / "sampling_design_inputs.csv"):
        n_formal = int(source["formal_sample_n"])
        n_val = int(source["validation_n"])
        pool = int(source["patient_pool_N"])
        sampling_rows.append(
            {
                **source,
                "formal_selection_probability": n_formal / pool,
                "formal_design_weight": pool / n_formal,
                "validation_selection_probability": n_val / pool,
                "validation_design_weight": pool / n_val,
                "sampling_unit": "patient",
            }
        )
    write_csv(OUTPUT / "SAMPLING_DESIGN.csv", sampling_rows, list(sampling_rows[0]))
    return {
        "validation_records": len(rows),
        "strict_validation_n": 86,
        "strict_positive_n": 20,
        "strict_negative_n": 66,
        "boundary_policy_validation_n": 143,
        "boundary_positive_counts": {"probable_positive": 77, "probable_negative": 20},
        "all_uncertain_policy_validation_n": 240,
        "all_uncertain_positive_counts": {"all_uncertain_positive": 174, "all_uncertain_negative": 20},
        "policy_counts": {
            row["policy"]: {
                "eligible_n": row["eligible_n"],
                "positive_n": row["positive_n"],
                "negative_n": row["negative_n"],
            }
            for row in policy_counts
        },
        "seed": REF_SEED,
        "bootstrap_replicates": REF_BOOT,
        "primary_phenotypes": list(CLINICAL_PHENOTYPES),
        "P3_reporting": "separate rule concordance table only",
    }


def make_transport_rows(data: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ctx = data["transport"]
    # Only the five prespecified contexts are accepted.
    if list(ctx) != ["MIMIC", "eICU", "NWICU", "SICdb", "HiRID"]:
        raise ValueError("Unexpected transport contexts")
    matrix: list[dict[str, object]] = []

    def add(context: str, phenotype: str, status: str, base_n: int, count: int | None, note: str) -> None:
        matrix.append(
            {
                "context": context,
                "phenotype": phenotype,
                "status": status,
                "positive_yield": count,
                "analysis_unit_denominator": base_n,
                "yield_per_1000": count / base_n * 1000 if count is not None and base_n else None,
                "interpretation": note,
            }
        )

    m = ctx["MIMIC"]
    for p, status, note in (
        ("P0", "direct", "source benchmark cohort"),
        ("P1", "direct", "source benchmark cohort"),
        ("P2", "direct", "source benchmark cohort"),
        ("P3", "rule_concordance_only", "shared evidence rules; not independent clinical performance"),
        ("P4", "definitionally_equivalent_to_P3", "weighted threshold reduces to the same binary rule"),
    ):
        count = int(m["yield"]["P3"]) if p == "P4" else int(m["yield"][p])
        add("MIMIC", p, status, int(m["base_n"]), count, note)

    e = ctx["eICU"]
    for p, status, count, note in (
        ("P0", "adapted", e["P0"], "mixed ICD-9/10 parser"),
        ("P1", "partial", e["P1"], "diagnosis-priority semantics not independently verified"),
        ("P2_direct", e["P2_direct_status"], None, "contemporaneous local ULN unavailable"),
        ("P2_proxy", "proxy", e["P2_proxy"], "fixed literature threshold; not a site-specific ULN"),
        ("P3", e["P3_status"], None, "required domains are absent or semantically unsupported"),
        ("P4", e["P4_status"], None, "required evidence domains unavailable"),
    ):
        add("eICU", p, status, int(e["base_n"]), count, note)

    n = ctx["NWICU"]
    for p, status, count, note in (
        ("P0", "direct", n["P0"], "ICD-10 any-position"),
        ("P1", "partial", n["P1"], "seq_num 0/1 primary semantics remain unverified"),
        ("P2", "direct", n["P2"], "row-specific ULN; unit/reference pairing requires audit"),
        ("P3", n["P3_status"], None, "free text and imaging unavailable"),
        ("P4", n["P4_status"], None, "free text and imaging unavailable"),
    ):
        add("NWICU", p, status, int(n["base_n"]), count, note)

    s = ctx["SICdb"]
    for p, status, count, note in (
        ("P0", s["P0_status"], s["P0"], "only principal diagnosis is available; partial any-position mapping"),
        ("P1", s["P1_status"], s["P1"], "principal ICD-10 field"),
        ("P2", s["P2_status"], None, "contemporaneous ULN unavailable"),
        ("P3", s["P3_P4_status"], None, "text and imaging unavailable"),
        ("P4", s["P3_P4_status"], None, "text and imaging unavailable"),
    ):
        add("SICdb", p, status, int(s["base_n"]), count, note)

    h = ctx["HiRID"]
    for p, status, note in (
        ("P0", "not_identifiable", "diagnostic domain absent; do not encode as negative"),
        ("P1", "not_identifiable", "diagnostic domain absent; do not encode as negative"),
        ("P2", "not_identifiable", "diagnostic domain absent"),
        ("P3", "not_computable", "required enzyme/text/imaging anchors absent"),
        ("P4", "not_identifiable", "required diagnostic evidence absent"),
    ):
        add("HiRID", p, status, int(h["base_n"]), None, note)

    e_decomp = e["P0_P2_decomposition"]
    e_both = int(e_decomp["both"])
    e_only_p0 = int(e_decomp["only_P0"])
    e_only_p2 = int(e_decomp["only_P2"])
    if (e_both, e_only_p0, e_only_p2) != (int(e["P2_proxy"]), int(e["P0"]) - int(e["P2_proxy"]), 0):
        raise ValueError("eICU P0/P2 decomposition does not reconcile")
    ncu = int(n["P0"])
    np2 = int(n["P2"])
    retention = [
        {
            "context": "eICU",
            "p0_status": "adapted",
            "p2_status": "proxy",
            "analysis_unit_denominator": int(e["base_n"]),
            "p0_n": int(e["P0"]),
            "p2_n": int(e["P2_proxy"]),
            "p0_to_p2_retention": e_both / int(e["P0"]),
            "p0_excluded_after_p2": e_only_p0,
            "p2_outside_p0": e_only_p2,
            "nesting_check": "aggregate decomposition: both=484, only P0=183, only P2=0",
        },
        {
            "context": "NWICU",
            "p0_status": "direct",
            "p2_status": "direct",
            "analysis_unit_denominator": int(n["base_n"]),
            "p0_n": ncu,
            "p2_n": np2,
            "p0_to_p2_retention": np2 / ncu,
            "p0_excluded_after_p2": ncu - np2,
            "p2_outside_p0": 0,
            "nesting_check": "constructive source-code definition: P2 = ap_any intersect enz_ge3; no separate row-level cross-tab in the staged artifact",
        },
    ]
    write_csv(
        OUTPUT / "TRANSPORT_COMPUTABILITY.csv",
        matrix,
        ["context", "phenotype", "status", "positive_yield", "analysis_unit_denominator", "yield_per_1000", "interpretation"],
    )
    write_csv(
        OUTPUT / "P0_TO_P2_RETENTION.csv",
        retention,
        ["context", "p0_status", "p2_status", "analysis_unit_denominator", "p0_n", "p2_n", "p0_to_p2_retention", "p0_excluded_after_p2", "p2_outside_p0", "nesting_check"],
    )
    return matrix, retention


def run_downstream(data: dict[str, object]) -> dict[str, object]:
    rows = read_csv(INPUT / "mimic_patient_cluster_counts.csv")
    columns = [f"{x}_{p}" for p in PHENOTYPES for x in ("n", "d")]
    if any(column not in rows[0] for column in columns):
        raise ValueError("Missing per-patient phenotype outcome counts")
    if len({r["cluster_token"] for r in rows}) != len(rows):
        raise ValueError("Duplicate anonymous patient-cluster tokens")
    totals = {p: {"n": 0, "deaths": 0} for p in PHENOTYPES}
    for row in rows:
        for p in PHENOTYPES:
            totals[p]["n"] += int(row[f"n_{p}"])
            totals[p]["deaths"] += int(row[f"d_{p}"])
    expected = {p: {"n": int(data["transport"]["MIMIC"]["yield"][p]), "deaths": int(data["transport"]["MIMIC"]["deaths"][p])} for p in PHENOTYPES}
    if totals != expected:
        raise ValueError(f"Staged cluster counts fail source reconciliation: {totals}")

    # Verify nested membership and patient cluster counts before resampling.
    p0_only = sum(int(r["n_P0"]) > 0 and int(r["n_P1"]) == 0 for r in rows)
    p1_outside_p0 = sum(int(r["n_P1"]) > 0 and int(r["n_P0"]) == 0 for r in rows)
    if p1_outside_p0 != 0 or totals["P1"]["n"] > totals["P0"]["n"]:
        raise ValueError("P1 membership is not nested within P0")

    rng = np.random.default_rng(DOWNSTREAM_SEED)
    contrasts = [("P0", "P1"), ("P0", "P2"), ("P0", "P3"), ("P2", "P3")]
    result_rows: list[dict[str, object]] = []
    for a, b in contrasts:
        union = [r for r in rows if int(r[f"n_{a}"]) > 0 or int(r[f"n_{b}"]) > 0]
        k = len(union)
        if not k:
            raise ValueError(f"Empty patient union for {a}/{b}")
        n_a = sum(int(r[f"n_{a}"]) for r in union)
        d_a = sum(int(r[f"d_{a}"]) for r in union)
        n_b = sum(int(r[f"n_{b}"]) for r in union)
        d_b = sum(int(r[f"d_{b}"]) for r in union)
        point_a = d_a / n_a
        point_b = d_b / n_b
        draws: list[float] = []
        token_array = np.array([r["cluster_token"] for r in union], dtype=str)
        for _ in range(DOWNSTREAM_BOOT):
            sampled_tokens = rng.choice(token_array, size=k, replace=True)
            multiplicity = Counter(sampled_tokens.tolist())
            boot_n_a = boot_d_a = boot_n_b = boot_d_b = 0
            for row in union:
                copies = multiplicity.get(row["cluster_token"], 0)
                if copies:
                    boot_n_a += copies * int(row[f"n_{a}"])
                    boot_d_a += copies * int(row[f"d_{a}"])
                    boot_n_b += copies * int(row[f"n_{b}"])
                    boot_d_b += copies * int(row[f"d_{b}"])
            if boot_n_a and boot_n_b:
                draws.append(boot_d_b / boot_n_b - boot_d_a / boot_n_a)
        d = np.asarray(draws, dtype=float)
        result_rows.append(
            {
                "comparison": f"{b}_minus_{a}",
                "phenotype_A": a,
                "phenotype_B": b,
                "unit": "patient-level paired cluster bootstrap; admissions retained within sampled patient",
                "patients_in_union": k,
                "admissions_A": n_a,
                "deaths_A": d_a,
                "mortality_A": point_a,
                "admissions_B": n_b,
                "deaths_B": d_b,
                "mortality_B": point_b,
                "point_difference_B_minus_A": point_b - point_a,
                "bootstrap_median": float(np.median(d)),
                "ci_lower": float(np.quantile(d, 0.025)),
                "ci_upper": float(np.quantile(d, 0.975)),
                "ci_level": 0.95,
                "ci_method": "paired patient-cluster percentile bootstrap with draw multiplicity preserved",
                "bootstrap_replicates": DOWNSTREAM_BOOT,
                "seed": DOWNSTREAM_SEED,
            }
        )
    write_csv(
        OUTPUT / "MIMIC_PAIRED_DOWNSTREAM_BOOTSTRAP.csv",
        result_rows,
        list(result_rows[0]),
    )
    old = data["downstream_prior"]
    p01 = next(row for row in result_rows if row["comparison"] == "P1_minus_P0")
    return {
        "base_admissions": int(old["base_n"]),
        "phenotype_death_totals_reconciled": totals,
        "P1_nested_in_P0": p1_outside_p0 == 0,
        "P0_only_patient_clusters": p0_only,
        "interval_P1_minus_P0": [p01["ci_lower"], p01["ci_upper"]],
        "point_difference_P1_minus_P0": p01["point_difference_B_minus_A"],
        "bootstrap_median_P1_minus_P0": p01["bootstrap_median"],
        "seed": DOWNSTREAM_SEED,
        "bootstrap_replicates": DOWNSTREAM_BOOT,
    }


def verify_no_sensitive_columns() -> None:
    for path in INPUT.glob("*.csv"):
        header = next(csv.reader(path.open("r", encoding="utf-8", newline="")), [])
        forbidden = {"hadm_id", "subject_id", "patientunitstayid", "hospitalid", "hospital_id", "cluster_id"}
        if forbidden.intersection(x.lower() for x in header):
            raise ValueError(f"Identifier-bearing input column found in {path.name}")


def main() -> None:
    reference_label_source = reference_label_source_from_manifest()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    verify_no_sensitive_columns()
    reference = run_reference()
    aggregate = json.loads((INPUT / "aggregate_context_inputs.json").read_text(encoding="utf-8"))
    matrix, retention = make_transport_rows(aggregate)
    downstream = run_downstream(aggregate)
    summary = {
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
            "threads": {k: __import__("os").environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        },
        "reference_analysis": reference,
        "transport_contexts": ["MIMIC", "eICU", "NWICU", "SICdb", "HiRID"],
        "transport_rows": len(matrix),
        "retention_rows": len(retention),
        "downstream_analysis": downstream,
        "reference_provenance": {
            "source_artifact_filename": reference_label_source["filename"],
            "source_artifact_path": reference_label_source["path"],
            "source_artifact_sha256": reference_label_source["sha256"],
            "adjudication_design": (
                "Two clinicians independently applied the frozen label manual; "
                "a third clinician adjudicated disagreements and ambiguous cases."
            ),
            "label_policies": [
                "strict",
                "probable_positive",
                "probable_negative",
                "all_uncertain_positive",
                "all_uncertain_negative",
            ],
            "primary_policy": "strict",
        },
        "limitations": [
            "eICU P2 is a fixed-threshold proxy, not a local-ULN implementation.",
            "NWICU P0-to-P2 nesting follows the source-code intersection definition; a separate row-level cross-tab was not staged.",
            "Transport yields describe operational execution, not clinical accuracy or disease prevalence.",
            "P3 is reported only as rule concordance; it is excluded from the clinical performance table.",
            "No patient or hospital identifiers are present in the staged inputs or aggregate outputs.",
        ],
    }
    (OUTPUT / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    delivered = {
        p.name: sha256(p)
        for p in sorted(OUTPUT.iterdir())
        if p.is_file() and p.name not in {"CHECKSUMS.sha256", "PROVENANCE.json", "run.log"}
    }
    manifest = {
        "input_sha256": {p.name: sha256(p) for p in sorted(INPUT.iterdir()) if p.is_file()},
        "script_sha256": sha256(Path(__file__)),
        "output_sha256": delivered,
    }
    lines = [f"{value}  {name}" for name, value in delivered.items()]
    (OUTPUT / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUTPUT / "PROVENANCE.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
