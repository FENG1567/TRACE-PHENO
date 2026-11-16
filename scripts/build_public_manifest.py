"""Create the public asset manifest and checksums; gate on the privacy scan."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from trace_pheno.validation import scan_public_tree

MANIFESTS = ROOT / "manifests"
EXCLUDED_PARTS = {".git", ".venv", "artifacts", "__pycache__", ".pytest_cache"}
GENERATED = {"PUBLIC_ASSET_MANIFEST.json", "CHECKSUMS.sha256"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def public_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix in {".pyc", ".pyo"}
            or any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
        ):
            continue
        files.append(path)
    return sorted(files)


def role(path: Path) -> str:
    top = path.relative_to(ROOT).parts[0]
    return {
        "src": "executable_code", "scripts": "workflow_code", "Reproducibility": "restricted_workflow_code", "tests": "test",
        "configs": "machine_readable_specification", "schemas": "schema",
        "data": "synthetic_or_aggregate_data", "results": "aggregate_result",
        "figures": "frozen_figure", "docs": "documentation",
    }.get(top, "repository_metadata")


def main() -> None:
    MANIFESTS.mkdir(exist_ok=True)

    # The privacy scan gates the build: any finding fails the run.
    findings = scan_public_tree(ROOT)
    status = "PASS" if not findings else "FAIL"

    assets = []
    for path in public_files():
        if path.name in GENERATED:
            continue
        assets.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "role": role(path),
            "public": True,
        })
    manifest = {
        "package": "TRACE-PHENO public reproducibility package",
        "version": "0.2.0",
        "asset_count": len(assets),
        "total_bytes": sum(item["bytes"] for item in assets),
        "contains_patient_level_data": False,
        "contains_hospital_identifiers": False,
        "assets": assets,
    }
    (MANIFESTS / "PUBLIC_ASSET_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    checksum_lines = []
    for path in public_files():
        if path.name == "CHECKSUMS.sha256":
            continue
        checksum_lines.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    (MANIFESTS / "CHECKSUMS.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "asset_count": len(assets), "bytes": manifest["total_bytes"]}, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
