"""Compact publication layouts for Supplementary Figures 1–2 and the graphical abstract."""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from layout_common import (
    DATA,
    P,
    REVISION,
    arrow,
    box,
    canvas,
    diagram,
    export,
    grid,
    panel,
    read_csv,
)

mpl.rcParams.update({
    "font.family": "Arial",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10,
    "font.weight": "bold",
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 1,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.pad": 4,
    "ytick.major.pad": 4,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})

POLICIES = [
    "strict",
    "probable_positive",
    "probable_negative",
    "all_uncertain_positive",
    "all_uncertain_negative",
]
POLICY_LABELS = [
    "Strict reference",
    "Probable positive",
    "Probable negative",
    "All uncertain positive",
    "All uncertain negative",
]


def supplementary_figure1() -> None:
    """Show final design-weighted P0–P2 sensitivity and specificity intervals."""
    metrics = read_csv(REVISION, "BENCHMARK_METRICS.csv")
    phenotypes = ["P0", "P1", "P2"]
    ordered = [(policy, phenotype) for policy in POLICIES for phenotype in phenotypes]
    by_metric = {}

    for metric in ("sensitivity", "specificity"):
        data = metrics[
            (metrics.scale == "design_weighted")
            & (metrics.metric == metric)
            & metrics.phenotype.isin(phenotypes)
            & metrics.policy.isin(POLICIES)
        ].copy()
        if len(data) != len(ordered) or data.duplicated(["policy", "phenotype"]).any():
            raise ValueError(
                f"Expected one weighted {metric} row for every P0–P2 by five-policy combination."
            )
        data = data.set_index(["policy", "phenotype"]).loc[ordered]
        for (policy, phenotype), row in data.iterrows():
            estimate, lower, upper = [
                float(row[column]) for column in ("estimate", "ci_lower", "ci_upper")
            ]
            if not 0 <= lower <= estimate <= upper <= 1:
                raise ValueError(
                    f"Invalid {metric} estimate or interval for {policy}/{phenotype}."
                )
        by_metric[metric] = data

    fig = canvas(6.8)
    fig.text(
        0.04,
        0.985,
        "Supplementary Figure 1 | Conditional sensitivity and specificity across label policies",
        fontsize=10.5,
        ha="left",
        va="top",
    )

    offsets = {"P0": -0.18, "P1": 0.0, "P2": 0.18}
    axes = []
    panel_specs = [
        (
            (0.035, 0.500, 0.930, 0.430),
            "A",
            "Sensitivity by reference-label policy",
            "sensitivity",
            (142, 36, 16, 35),
        ),
        (
            (0.035, 0.045, 0.930, 0.430),
            "B",
            "Specificity by reference-label policy",
            "specificity",
            (142, 55, 16, 35),
        ),
    ]
    for rect, label, title, metric, margins in panel_specs:
        ax = panel(fig, rect, label, title, margins=margins, title_size=11)
        data = by_metric[metric]
        for phenotype in phenotypes:
            for policy_index, policy in enumerate(POLICIES):
                row = data.loc[(policy, phenotype)]
                estimate, lower, upper = [
                    float(row[column]) for column in ("estimate", "ci_lower", "ci_upper")
                ]
                ax.errorbar(
                    estimate,
                    policy_index + offsets[phenotype],
                    xerr=[[estimate - lower], [upper - estimate]],
                    fmt="o",
                    color=P[phenotype],
                    label=phenotype if policy_index == 0 else "_nolegend_",
                    markersize=5.2,
                    capsize=3.0,
                    elinewidth=1.35,
                    markeredgewidth=1.1,
                )

        ax.set_yticks(np.arange(len(POLICIES)), POLICY_LABELS)
        ax.invert_yaxis()
        if metric == "sensitivity":
            ax.set_xlim(0.0, 0.40)
            ax.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4], ["0.00", "0.10", "0.20", "0.30", "0.40"])
            ax.set_xlabel("Design-weighted sensitivity (95% CI)")
        else:
            ax.set_xlim(0.92, 1.01)
            ax.set_xticks([0.92, 0.94, 0.96, 0.98, 1.00], ["0.92", "0.94", "0.96", "0.98", "1.00"])
            ax.set_xlabel("Design-weighted specificity (95% CI)")
        grid(ax, axis="x")
        axes.append(ax)

    axes[-1].legend(
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.28),
        borderaxespad=0,
        handlelength=1.1,
        columnspacing=2.0,
        markerscale=1.05,
    )
    export(fig, "Supplementary_Figure_1_Label_Policy_Sensitivity")


def supplementary_figure2() -> None:
    """Show design-weighted P3 rule concordance and the P3/P4 logic equivalence."""
    concordance = read_csv(REVISION, "P3_RULE_CONCORDANCE.csv")
    data = concordance[
        (concordance.scale == "design_weighted")
        & concordance.policy.isin(POLICIES)
    ].copy()
    if len(data) != len(POLICIES) or data.duplicated(["policy"]).any():
        raise ValueError("Expected one design-weighted P3 concordance row per reference-label policy.")
    data = data.set_index("policy").loc[POLICIES]

    fig = canvas(5.8)
    fig.text(
        0.04,
        0.985,
        "Supplementary Figure 2 | P3 calibration across label policies and P3/P4 equivalence",
        fontsize=10.5,
        ha="left",
        va="top",
    )

    ax = panel(
        fig,
        (0.035, 0.380, 0.930, 0.540),
        "A",
        "P3 rule concordance",
        margins=(143, 34, 146, 35),
        title_size=11,
    )
    for index, (policy, row) in enumerate(data.iterrows()):
        estimate, lower, upper = [
            float(row[column]) for column in ("rule_concordance", "ci_lower", "ci_upper")
        ]
        if not 0 <= lower <= estimate <= upper <= 1:
            raise ValueError(f"Invalid P3 concordance interval for {policy}.")
        ax.errorbar(
            estimate,
            index,
            xerr=[[estimate - lower], [upper - estimate]],
            fmt="o",
            color=P["P3"],
            markersize=6.0,
            capsize=3.0,
            elinewidth=1.4,
            markeredgewidth=1.1,
        )
        ax.text(
            1.035,
            index,
            f"{estimate:.3f} ({lower:.3f}–{upper:.3f})",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=9.5,
            color="#27313A",
        )

    ax.set_yticks(np.arange(len(POLICIES)), POLICY_LABELS)
    ax.invert_yaxis()
    ax.set_xlim(-0.02, 1.02)
    ax.set_xticks(np.arange(0.0, 1.01, 0.2), ["0.0", "0.2", "0.4", "0.6", "0.8", "1.0"])
    ax.set_xlabel("Design-weighted agreement with reference rule (95% CI)")
    grid(ax, axis="x")

    ax = diagram(
        fig,
        (0.035, 0.035, 0.930, 0.330),
        "B",
        "P3 and P4 equivalence",
        title_size=11,
    )

    box(ax, 0.12, 0.66, 0.30, 0.17, "P3 rule", fc="#FFF4E6", ec=P["P3"], fs=10)
    box(ax, 0.58, 0.66, 0.30, 0.17, "P4 score rule", fc="#F7F9FB", ec="#8293A3", fs=10)
    arrow(ax, (0.27, 0.63), (0.45, 0.49))
    arrow(ax, (0.73, 0.63), (0.55, 0.49))
    box(
        ax,
        0.21,
        0.11,
        0.58,
        0.38,
        "Same 2-of-3 rule\nAll three findings recorded\nas present or absent",
        fc="#E8F5E9",
        ec="#2A9D8F",
        fs=9.5,
    )
    export(fig, "Supplementary_Figure_2_P3_P4_Rule_Concordance")


def graphical_abstract() -> None:
    """Summarize cohort definitions and the descriptive P1–P0 outcome difference."""
    burden = read_csv(DATA, "Figure_5_Burden.csv").set_index("phenotype")
    drift = read_csv(REVISION, "MIMIC_PAIRED_DOWNSTREAM_BOOTSTRAP.csv").set_index("comparison")
    p0, p1 = burden.loc["P0"], burden.loc["P1"]
    difference = drift.loc["P1_minus_P0"]

    fig = canvas(5.0)
    fig.text(0.04, 0.985, "TRACE-PHENO", fontsize=13.5, color="#184E77", va="top", ha="left")
    fig.text(
        0.96,
        0.985,
        "Acute pancreatitis (AP)",
        fontsize=9.5,
        color="#4D5964",
        va="top",
        ha="right",
    )
    fig.text(
        0.04,
        0.925,
        "Evidence availability, phenotype rules and downstream conclusions",
        fontsize=10.5,
        color="#263238",
        va="top",
        ha="left",
    )
    fig.text(
        0.04,
        0.880,
        "Cohort size and observed mortality differ by diagnosis position",
        fontsize=9.5,
        color="#34495E",
        va="top",
        ha="left",
    )

    ax = diagram(
        fig,
        (0.035, 0.080, 0.435, 0.730),
        "A",
        "Evidence and definitions",
        title_size=10.5,
    )
    box(
        ax,
        0.03,
        0.67,
        0.94,
        0.27,
        "At least 2 of 3 findings\nTypical pain · enzymes ≥3× ULN\nCharacteristic imaging\nULN: upper limit of normal",
        fc="#EAF2F8",
        ec="#4C78A8",
        fs=9.3,
    )
    box(
        ax,
        0.03,
        0.42,
        0.94,
        0.20,
        "Five contexts: MIMIC · eICU · NWICU\nSICdb · HiRID",
        fc="#F7F9FB",
        ec="#718096",
        fs=9.5,
    )
    box(
        ax,
        0.03,
        0.08,
        0.94,
        0.26,
        "P0 any-position code · P1 principal code\nP2 P0 + enzyme ≥3× local ULN",
        fc="#FFF4E6",
        ec="#E69F00",
        fs=9.5,
    )
    ax = diagram(
        fig,
        (0.530, 0.080, 0.435, 0.730),
        "B",
        "Diagnosis position selects different cohorts",
        title_size=10.5,
    )
    box(
        ax,
        0.02,
        0.67,
        0.46,
        0.27,
        f"P0 any position\n{int(p0.admissions):,} admissions\n{int(p0.deaths)} deaths\n{p0.mortality_pct:.2f}% mortality",
        fc="#EAF2F8",
        ec=P["P0"],
        fs=9.2,
    )
    box(
        ax,
        0.52,
        0.67,
        0.46,
        0.27,
        f"P1 principal position\n{int(p1.admissions):,} admissions\n{int(p1.deaths)} deaths\n{p1.mortality_pct:.2f}% mortality",
        fc="#F7F9FB",
        ec=P["P1"],
        fs=9.2,
    )
    estimate = 100 * float(difference.point_difference_B_minus_A)
    lower = 100 * float(difference.ci_lower)
    upper = 100 * float(difference.ci_upper)
    box(
        ax,
        0.04,
        0.08,
        0.92,
        0.44,
        f"Observed mortality difference\nP1 − P0: {estimate:.2f} percentage points\n95% CI {lower:.2f} to {upper:.2f}",
        fc="#FFF4E6",
        ec="#D55E00",
        fs=9.7,
    )
    export(fig, "Graphical_Abstract")


def main() -> None:
    supplementary_figure1()
    supplementary_figure2()
    graphical_abstract()


if __name__ == "__main__":
    main()




