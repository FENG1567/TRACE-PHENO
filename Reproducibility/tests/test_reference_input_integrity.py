from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPRODUCIBILITY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPRODUCIBILITY_DIR))

from run_server_analysis import reference_label_source_from_manifest


class StagedReferenceInputIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name)
        self.manifest_path = self.input_dir / "input_manifest.json"
        self.validation_path = self.input_dir / "validation_inputs.csv"
        self.sampling_path = self.input_dir / "sampling_design_inputs.csv"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_valid_bundle(self) -> None:
        validation_bytes = b"stratum,final_label\nsynthetic,non_AP\n"
        sampling_bytes = b"stratum,patient_pool_N\nsynthetic,1\n"
        self.validation_path.write_bytes(validation_bytes)
        self.sampling_path.write_bytes(sampling_bytes)
        label_digest = "a" * 64
        manifest = {
            "reference": {
                "reference_label_source": {
                    "filename": "SYNTHETIC_REFERENCE_LABEL_SET.csv",
                    "path": "03_reference_standard/SYNTHETIC_REFERENCE_LABEL_SET.csv",
                    "sha256": label_digest,
                },
                "source_hashes": {"SYNTHETIC_REFERENCE_LABEL_SET.csv": label_digest},
                "validation_inputs.csv": {
                    "rows": 1,
                    "sha256": hashlib.sha256(validation_bytes).hexdigest(),
                },
                "sampling_design_inputs.csv": {
                    "rows": 1,
                    "sha256": hashlib.sha256(sampling_bytes).hexdigest(),
                },
            }
        }
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_matching_staged_reference_files_pass_hash_validation(self) -> None:
        self.write_valid_bundle()

        source = reference_label_source_from_manifest(self.manifest_path)

        self.assertEqual(source["filename"], "SYNTHETIC_REFERENCE_LABEL_SET.csv")

    def test_changed_validation_csv_is_rejected(self) -> None:
        self.write_valid_bundle()
        self.validation_path.write_bytes(b"changed synthetic validation bytes\n")

        with self.assertRaisesRegex(ValueError, "validation_inputs.csv SHA-256"):
            reference_label_source_from_manifest(self.manifest_path)

    def test_missing_validation_csv_is_rejected(self) -> None:
        self.write_valid_bundle()
        self.validation_path.unlink()

        with self.assertRaisesRegex(FileNotFoundError, "validation_inputs.csv"):
            reference_label_source_from_manifest(self.manifest_path)

    def test_changed_sampling_design_csv_is_rejected(self) -> None:
        self.write_valid_bundle()
        self.sampling_path.write_bytes(b"changed synthetic sampling bytes\n")

        with self.assertRaisesRegex(ValueError, "sampling_design_inputs.csv SHA-256"):
            reference_label_source_from_manifest(self.manifest_path)


if __name__ == "__main__":
    unittest.main()
