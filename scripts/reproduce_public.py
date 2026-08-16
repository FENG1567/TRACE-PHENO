"""One-command public reproduction: tests, synthetic analyses, cards, figures, audit."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + ENV.get("PYTHONPATH", "")
ENV["PYTHONDONTWRITEBYTECODE"] = "1"


def run(command: list[str]) -> dict[str, object]:
    process = subprocess.run(command, cwd=ROOT, env=ENV, text=True, capture_output=True)
    print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, file=sys.stderr, end="")
    if process.returncode:
        raise SystemExit(process.returncode)
    return {"command": command, "returncode": process.returncode}


def main() -> None:
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "trace_pheno.cli", "synthetic"],
        [sys.executable, "-m", "trace_pheno.cli", "equivalence"],
        [sys.executable, "-m", "trace_pheno.cli", "cards"],
        [sys.executable, "scripts/build_figures.py"],
        [sys.executable, "-m", "trace_pheno.cli", "validate"],
    ]
    executed = [run(command) for command in commands]
    report = {
        "status": "PASS",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "commands": executed,
        "scope": "public synthetic and aggregate reproduction; no clinical records",
    }
    out = ROOT / "artifacts" / "REPRODUCTION_REPORT.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"public reproduction PASS: {out}")
    run([sys.executable, "scripts/build_public_manifest.py"])


if __name__ == "__main__":
    main()
