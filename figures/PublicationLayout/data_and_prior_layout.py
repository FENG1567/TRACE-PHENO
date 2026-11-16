from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Patch


OUT = Path(__file__).resolve().parent
BUNDLED = OUT / "source_data"
REVISION = BUNDLED / "revision"
DATA = BUNDLED / "frozen"
OLD_SOURCE = BUNDLED / "legacy"

P = {"P0": "#0072B2", "P1": "#56B4E9", "P2": "#E69F00", "P3": "#D55E00"}
STATUS = {
    "direct": "#2A9D8F", "adapted": "#4C78A8", "partial": "#F2CC8F",
    "proxy": "#E07A5F", "not-computable": "#D1D5D8",
    "not-identifiable": "#6C757D", "excluded": "#222222",
}
CAPABILITY = {
    "absent": "#D9DEE2", "unknown": "#AEB8C2", "proxy": "#E07A5F",
    "partial": "#F2CC8F", "compatible": "#72A0C1", "exact": "#2A9D8F",
}

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8.0,
    "axes.titlesize": 9.0,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.2,
    "ytick.labelsize": 7.2,
    "legend.fontsize": 7.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.75,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "legend.frameon": False,
    "savefig.facecolor": "white",
})


def read_csv(folder: Path, filename: str) -> pd.DataFrame:
    path = folder / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required aggregate input is missing: {filename}")
    return pd.read_csv(path)


def read_json(folder: Path, filename: str) -> dict:
    path = folder / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required aggregate input is missing: {filename}")
    return json.loads(path.read_text(encoding="utf-8-sig"))

