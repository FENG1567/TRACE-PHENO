"""Verify every file recorded in manifests/CHECKSUMS.sha256."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    failures = []
    manifest = ROOT / "manifests" / "CHECKSUMS.sha256"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")
        elif digest(path) != expected:
            failures.append(f"mismatch: {relative}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("checksum verification PASS")


if __name__ == "__main__":
    main()

