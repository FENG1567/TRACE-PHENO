"""Regenerate six public manuscript figures from aggregate or schematic sources."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "aggregate" / "figure_source"
SUPP = ROOT / "results" / "supplementary_tables"

COLORS = {"P0": "#0072B2", "P1": "#E69F00", "P2": "#009E73", "P3": "#CC79A7", "P5": "#56B4E9"}
STATUS_COLORS = {
    "direct": "#009E73", "adapted": "#56B4E9", "partial": "#E69F00", "proxy": "#D55E00",
    "not-computable": "#9A9A9A", "not-identifiable": "#222222", "equivalent-to-P3": "#CC79A7",
    "direct-exploratory": "#0072B2", "excluded": "#D55E00",
}


def panel(ax, label: str, title: str) -> None:
    ax.text(-0.08, 1.05, label, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top")
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold")


def box(ax, x: float, y: float, text: str, color: str = "#E8F1F8", width: float = 0.23) -> None:
    patch = FancyBboxPatch((x - width / 2, y - 0.07), width, 0.14, boxstyle="round,pad=0.02", fc=color, ec="#354052", lw=1)
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=8)


def arrow(ax, x1: float, y1: float, x2: float, y2: float) -> None:
    ax.annotate("", (x2, y2), (x1, y1), arrowprops={"arrowstyle": "->", "color": "#354052", "lw": 1.1})


def save(fig, out: Path, stem: str, alt: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{stem}.{ext}", dpi=300 if ext == "png" else None, bbox_inches="tight")
    (out / f"{stem}_ALT_TEXT.txt").write_text(alt.strip() + "\n", encoding="utf-8")
    plt.close(fig)


def figure1(out: Path) -> None:
    roles = pd.read_csv(SUPP / "Supplementary_Table_1_Data_Roles.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    ax = axes[0, 0]; panel(ax, "A", "Measurement chain")
    labels = ["Evidence\navailability", "Phenotype\ndefinition", "Cohort\nmembership", "Downstream\nconclusion"]
    for i, label in enumerate(labels):
        box(ax, 0.13 + i * 0.25, 0.5, label, width=0.19)
        if i < len(labels) - 1: arrow(ax, 0.23 + i * 0.25, 0.5, 0.28 + i * 0.25, 0.5)
    ax.text(0.5, 0.17, "Missing evidence is not a negative finding", ha="center", color="#D55E00", fontsize=9)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[0, 1]; panel(ax, "B", "Eight-stage audit trail")
    stages = ["Inventory", "Freeze", "Reference", "Benchmark", "Transport", "Impact", "Generic", "Release"]
    for i, label in enumerate(stages):
        x, y = 0.13 + (i % 4) * 0.25, 0.68 - (i // 4) * 0.38
        box(ax, x, y, label, width=0.18)
        if i not in (3, 7): arrow(ax, x + 0.10, y, x + 0.15, y)
    arrow(ax, 0.88, 0.61, 0.88, 0.37); arrow(ax, 0.88, 0.30, 0.78, 0.30)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[1, 0]; panel(ax, "C", "Predefined database roles")
    labels = roles["Database"].astype(str).tolist()
    y = np.arange(len(labels))
    ax.barh(y, np.ones(len(labels)), color=["#0072B2", "#56B4E9", "#009E73", "#E69F00", "#777777", "#D55E00"][:len(labels)])
    ax.set_yticks(y, labels); ax.set_xlim(0, 1); ax.set_xticks([]); ax.invert_yaxis()
    for i, role in enumerate(roles["Role"].astype(str)): ax.text(0.02, i, role, va="center", fontsize=7, color="white")
    ax.spines[:].set_visible(False)

    ax = axes[1, 1]; panel(ax, "D", "Public and credentialled reproducibility layers")
    for y0, text, color in [(0.75, "Public: code, schema, synthetic data", "#DDEBF7"), (0.50, "Public: aggregate registry and figures", "#E2F0D9"), (0.25, "Restricted: row-level clinical reconstruction", "#FCE4D6")]:
        box(ax, 0.5, y0, text, color=color, width=0.66)
    arrow(ax, 0.5, 0.67, 0.5, 0.58); arrow(ax, 0.5, 0.42, 0.5, 0.33)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.tight_layout()
    save(fig, out, "Figure_1_Study_Design", "Four panels show the measurement chain, eight audit stages, predefined database roles, and public versus credentialled reproduction layers.")


def figure2(out: Path) -> None:
    labels = pd.read_csv(ROOT / "data" / "aggregate" / "benchmark" / "VALIDATION_LABEL_POLICY_COUNTS.csv")
    sample = pd.read_csv(ROOT / "data" / "aggregate" / "benchmark" / "SAMPLING_DESIGN_REVISION2.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    ax = axes[0]; panel(ax, "A", "AP target construct")
    for x, text in zip((0.18, 0.50, 0.82), ("Compatible\npain", "Enzyme\n≥3× local ULN", "Compatible\nimaging")):
        box(ax, x, 0.62, text, width=0.25)
    ax.text(0.5, 0.25, "Definitive construct: ≥2 evidence domains\nAvailability, polarity, time, source, provenance", ha="center", fontsize=8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[1]; panel(ax, "B", "Stratified patient sampling")
    ax.bar(sample["stratum"], sample["validation_n"], color="#56B4E9", label="validation")
    ax.bar(sample["stratum"], sample["development_n"], bottom=sample["validation_n"], color="#0072B2", label="development")
    ax.set_ylabel("Sampled patients"); ax.tick_params(axis="x", rotation=30); ax.legend(frameon=False, fontsize=8)

    ax = axes[2]; panel(ax, "C", "Validation eligibility by label policy")
    val = labels[labels["split"].eq("validation")].copy()
    ax.bar(val["policy"], val["positive_n"], color="#D55E00", label="positive")
    ax.bar(val["policy"], val["negative_n"], bottom=val["positive_n"], color="#999999", label="negative")
    ax.set_ylabel("Eligible records"); ax.tick_params(axis="x", rotation=35); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    save(fig, out, "Figure_2_Construct_and_Reference", "Panels show the three AP evidence domains, stratified patient sampling, and policy-specific validation eligibility. The reference set was constructed by two experienced surgical clinicians who adjudicated independently in a blinded manner, with a third surgical clinician resolving disagreements.")


def figure3(out: Path) -> None:
    metrics = pd.read_csv(SOURCE / "Figure_3_Strict_Metrics.csv")
    boundary = pd.read_csv(SOURCE / "Figure_3_Label_Boundary.csv")
    p3 = pd.read_csv(SOURCE / "Figure_3_P3_Sensitivity.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    ax = axes[0]; panel(ax, "A", "Strict conditional agreement")
    sub = metrics[metrics["metric"].isin(["sensitivity", "specificity"])].copy()
    phenos = [p for p in ("P0", "P1", "P2", "P3", "P5") if p in set(sub["phenotype"])]
    offsets = {"sensitivity": -0.12, "specificity": 0.12}
    for metric in ("sensitivity", "specificity"):
        m = sub[sub["metric"].eq(metric)].set_index("phenotype").reindex(phenos)
        y = np.arange(len(phenos)) + offsets[metric]
        ax.errorbar(m["estimate"], y, xerr=[m["estimate"] - m["ci_lower"], m["ci_upper"] - m["estimate"]], fmt="o", label=metric, capsize=2)
    ax.set_yticks(np.arange(len(phenos)), phenos); ax.set_xlim(-0.02, 1.02); ax.set_xlabel("Design-weighted estimate (95% CI)"); ax.legend(frameon=False, fontsize=8)
    ax.text(0.02, -0.22, "Blinded two-clinician reference; n=86, 20 positive; precision limited", transform=ax.transAxes, fontsize=7)

    ax = axes[1]; panel(ax, "B", "Sensitivity across label boundaries")
    b = boundary[boundary["metric"].eq("sensitivity")]
    pivot = b.pivot(index="phenotype", columns="policy", values="estimate")
    pivot.plot(kind="bar", ax=ax, color=["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#777777"][:len(pivot.columns)])
    ax.set_ylim(0, 1.05); ax.set_ylabel("Sensitivity"); ax.set_xlabel(""); ax.legend(frameon=False, fontsize=6, title=None)

    ax = axes[2]; panel(ax, "C", "P3 implementation sensitivity analyses")
    s = p3[p3["metric"].eq("sensitivity")]
    y = np.arange(len(s))
    ax.errorbar(s["estimate"], y, xerr=[s["estimate"] - s["ci_lower"], s["ci_upper"] - s["estimate"]], fmt="o", color="#CC79A7", capsize=2)
    ax.set_yticks(y, s["variant"]); ax.set_xlim(0, 1.02); ax.set_xlabel("Sensitivity (95% CI)")
    ax.text(0.02, -0.22, "P3 is rule-concordant with reference construction; P4 is not independent", transform=ax.transAxes, fontsize=7)
    fig.tight_layout()
    save(fig, out, "Figure_3_Conditional_Agreement", "Forest and bar plots show precision-limited conditional agreement against the reference set (blinded two-clinician adjudication), label-boundary sensitivity, and P3 implementation sensitivity analyses.")


def figure4(out: Path) -> None:
    status = pd.read_csv(SOURCE / "fig4_transport_status.csv", index_col=0)
    capabilities = pd.read_csv(SOURCE / "fig4_capabilities.csv", index_col=0)
    failures = pd.read_csv(SOURCE / "fig4_d0_d6.csv")
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    ax = axes[0]; panel(ax, "A", "Transport status")
    statuses = list(STATUS_COLORS)
    matrix = status.map(lambda x: statuses.index(x) if x in statuses else -1).to_numpy()
    ax.imshow(matrix, cmap=ListedColormap([STATUS_COLORS[s] for s in statuses]), vmin=0, vmax=len(statuses)-1, aspect="auto")
    ax.set_xticks(range(len(status.columns)), status.columns); ax.set_yticks(range(len(status.index)), status.index)
    for i in range(status.shape[0]):
        for j in range(status.shape[1]): ax.text(j, i, status.iloc[i, j].replace("not-", "not\n"), ha="center", va="center", fontsize=5.8, color="white" if matrix[i, j] in (5, 6) else "black")

    ax = axes[1]; panel(ax, "B", "Evidence capability (not performance)")
    cap_levels = ["absent", "unknown", "proxy", "partial", "compatible", "exact"]
    cap_colors = ["#333333", "#BBBBBB", "#D55E00", "#E69F00", "#56B4E9", "#009E73"]
    cap_matrix = capabilities.map(lambda x: cap_levels.index(x) if x in cap_levels else 1).to_numpy()
    ax.imshow(cap_matrix, cmap=ListedColormap(cap_colors), vmin=0, vmax=len(cap_levels)-1, aspect="auto")
    ax.set_xticks(range(len(capabilities.columns)), capabilities.columns, rotation=60, ha="right", fontsize=7); ax.set_yticks(range(len(capabilities.index)), capabilities.index)
    for i in range(capabilities.shape[0]):
        for j in range(capabilities.shape[1]): ax.text(j, i, capabilities.iloc[i, j], ha="center", va="center", fontsize=5.5)

    ax = axes[2]; panel(ax, "C", "D0–D6 failure contexts")
    ax.bar(failures["failure"], failures["affected_database_contexts"], color="#0072B2")
    ax.set_ylabel("Affected database contexts"); ax.set_xlabel("Non-mutually-exclusive failure code")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    save(fig, out, "Figure_4_Transportability", "Panels show direct, adapted, partial, proxy, not-computable and not-identifiable transport states; evidence capability; and non-mutually-exclusive D0–D6 failures. ")


def figure5(out: Path) -> None:
    burden = pd.read_csv(SOURCE / "Figure_5_Burden.csv")
    sets = pd.read_csv(SOURCE / "Figure_5_Set_Decomposition.csv")
    drift = pd.read_csv(SOURCE / "Figure_5_Mortality_Drift.csv")
    report = pd.read_csv(SOURCE / "Figure_5_Reportability.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    ax = axes[0, 0]; panel(ax, "A", "MIMIC phenotype-positive burden")
    ax.bar(burden["phenotype"], burden["yield_per_1000"], color=[COLORS.get(p, "#999999") for p in burden["phenotype"]])
    ax.set_ylabel("Phenotype-positive yield per 1,000 admissions")
    for i, row in burden.iterrows(): ax.text(i, row["yield_per_1000"], f"n={int(row['admissions']):,}", ha="center", va="bottom", fontsize=7)

    ax = axes[0, 1]; panel(ax, "B", "Cohort set decomposition")
    s = sets[sets["comparison"].eq("P0 vs P3")]
    ax.bar(s["set_component"], s["n"], color=["#56B4E9", "#0072B2", "#CC79A7"])
    ax.set_ylabel("Admissions"); ax.tick_params(axis="x", rotation=25)

    ax = axes[1, 0]; panel(ax, "C", "Mortality conclusion drift")
    y = np.arange(len(drift))
    ax.errorbar(drift["risk_difference_pp"], y, xerr=[drift["risk_difference_pp"] - drift["ci_lower_pp"], drift["ci_upper_pp"] - drift["risk_difference_pp"]], fmt="o", color="#0072B2", capsize=3)
    ax.axvline(0, color="black", lw=0.8); mcid = float(drift["mcid_pp"].iloc[0]); ax.axvline(mcid, color="#D55E00", ls="--"); ax.axvline(-mcid, color="#D55E00", ls="--")
    ax.set_yticks(y, drift["comparison"]); ax.set_xlabel("Mortality risk difference (percentage points, 95% CI)")

    ax = axes[1, 1]; panel(ax, "D", "eICU hospital reportability")
    ax.bar(report["phenotype"], report["reportable_hospitals"], color=["#0072B2", "#E69F00", "#009E73"])
    ax.set_ylabel("Hospitals with ≥10 phenotype-positive stays")
    ax.text(0.02, 0.98, "Aggregate counts only; no hospital identifiers or quality ranking", transform=ax.transAxes, fontsize=7, va="top")
    fig.tight_layout()
    save(fig, out, "Figure_5_Downstream_Consequences", "Panels show phenotype-positive burden, cohort-set decomposition, mortality risk-difference drift with ±1 percentage-point thresholds, and aggregate eICU hospital reportability.")


def figure6(out: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.0))
    ax = axes[0]; panel(ax, "A", "Disease-generic object model")
    nodes = [(0.2, 0.75, "Target\nconstruct"), (0.5, 0.75, "Evidence\nassertion"), (0.8, 0.75, "Phenotype\ndefinition"), (0.2, 0.30, "Execution\nresult"), (0.5, 0.30, "Migration\nevent"), (0.8, 0.30, "Data card")]
    for x, y, text in nodes: box(ax, x, y, text, width=0.23)
    arrow(ax, 0.31, 0.75, 0.38, 0.75); arrow(ax, 0.61, 0.75, 0.68, 0.75); arrow(ax, 0.8, 0.66, 0.8, 0.39); arrow(ax, 0.69, 0.30, 0.61, 0.30); arrow(ax, 0.39, 0.30, 0.31, 0.30)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[1]; panel(ax, "B", "Equivalence and versioning")
    box(ax, 0.22, 0.65, "Rule AST", width=0.26); box(ax, 0.5, 0.65, "Canonical\nhash", width=0.26); box(ax, 0.78, 0.65, "Equivalence\nclass", width=0.26)
    arrow(ax, 0.36, 0.65, 0.37, 0.65); arrow(ax, 0.64, 0.65, 0.65, 0.65)
    ax.text(0.5, 0.25, "P3 ≡ P4 for complete binary inputs\nNo duplicate algorithm claim", ha="center", fontsize=8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[2]; panel(ax, "C", "AP and synthetic AKI reuse")
    box(ax, 0.25, 0.70, "AP: pain + enzyme\n+ imaging", color="#FCE4D6", width=0.38)
    box(ax, 0.75, 0.70, "AKI: creatinine + urine\n+ rolling windows", color="#E2F0D9", width=0.38)
    box(ax, 0.50, 0.30, "Shared evidence, time, missingness,\nmigration and data-card interfaces", width=0.62)
    arrow(ax, 0.30, 0.60, 0.43, 0.39); arrow(ax, 0.70, 0.60, 0.57, 0.39)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.tight_layout()
    save(fig, out, "Figure_6_Generic_Framework", "Panels show disease-generic audit objects, rule equivalence/versioning, and reuse of the same evidence and time interfaces for AP and a synthetic AKI demonstration.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "figures")
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    for fn in (figure1, figure2, figure3, figure4, figure5, figure6):
        fn(args.out)
    print(f"wrote public figures to {args.out}")


if __name__ == "__main__":
    main()
