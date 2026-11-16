"""Run the public checks and rebuilds: tests, synthetic analyses, cards, figures, checks."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + ENV.get("PYTHONPATH", "")
ENV["PYTHONDONTWRITEBYTECODE"] = "1"


def run(command: list[str]) -> None:
    process = subprocess.run(command, cwd=ROOT, env=ENV, text=True, capture_output=True)
    print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, file=sys.stderr, end="")
    if process.returncode:
        raise SystemExit(process.returncode)


def main() -> None:
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "trace_pheno.cli", "synthetic"],
        [sys.executable, "-m", "trace_pheno.cli", "equivalence"],
        [sys.executable, "-m", "trace_pheno.cli", "cards"],
        [sys.executable, "scripts/build_figures.py"],
        [sys.executable, "Reproducibility/check_cohort_summary.py"],
        [sys.executable, "scripts/check_release.py"],
        [sys.executable, "-m", "trace_pheno.cli", "validate"],
    ]
    for command in commands:
        run(command)
    print("public reproduction PASS")
    run([sys.executable, "scripts/build_public_manifest.py"])


if __name__ == "__main__":
    main()
