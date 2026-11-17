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
from stage_inputs import resolve_reference_labels


LABEL_HEADER = "review_case_id,variant,final_label\n"


class ReferenceInputSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ref_dir = Path(self.temp_dir.name) / "03_reference_standard"
        self.ref_dir.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_candidate(self, filename: str, contents: str = LABEL_HEADER) -> Path:
        path = self.ref_dir / filename
        path.write_text(contents, encoding="utf-8")
        return path

    def test_explicit_choice_selects_one_of_four_candidates(self) -> None:
        candidates = [
            "REFERENCE_LABEL_SET.csv",
            "ARCHIVED_REFERENCE_LABEL_SET.csv",
            "REFERENCE_LABEL_SET_backup.csv",
            "REVIEWED_REFERENCE_LABEL_SET.csv",
        ]
        for filename in candidates:
            self.write_candidate(filename)

        selected = resolve_reference_labels(self.ref_dir, "REVIEWED_REFERENCE_LABEL_SET.csv")

        self.assertEqual(selected.name, "REVIEWED_REFERENCE_LABEL_SET.csv")

    def test_nonexistent_explicit_path_is_actionable(self) -> None:
        with self.assertRaises(FileNotFoundError) as caught:
            resolve_reference_labels(self.ref_dir, "missing_REFERENCE_LABEL_SET.csv")

        self.assertIn("--reference-label-file", str(caught.exception))
        self.assertIn("missing_REFERENCE_LABEL_SET.csv", str(caught.exception))

    def test_unambiguous_default_selects_the_only_candidate(self) -> None:
        candidate = self.write_candidate("FINAL_REFERENCE_LABEL_SET.csv")

        self.assertEqual(resolve_reference_labels(self.ref_dir), candidate.resolve())

    def test_ambiguous_default_refuses_to_prefer_canonical_name(self) -> None:
        self.write_candidate("REFERENCE_LABEL_SET.csv", "")
        self.write_candidate("REFERENCE_LABEL_SET_backup.csv", "")

        with self.assertRaises(ValueError) as caught:
            resolve_reference_labels(self.ref_dir)

        message = str(caught.exception)
        self.assertIn("ambiguous", message)
        self.assertIn("REFERENCE_LABEL_SET.csv", message)
        self.assertIn("REFERENCE_LABEL_SET_backup.csv", message)
        self.assertIn("--reference-label-file", message)

    def test_explicit_file_requires_expected_csv_header(self) -> None:
        invalid = self.write_candidate("custom.csv", "review_case_id,final_label\n")

        with self.assertRaisesRegex(ValueError, "missing required columns"):
            resolve_reference_labels(self.ref_dir, invalid.name)

    def test_analysis_provenance_uses_staged_filename_path_and_hash(self) -> None:
        digest = "a" * 64
        manifest_path = Path(self.temp_dir.name) / "input_manifest.json"
        validation_bytes = b"stratum,final_label\nsynthetic,non_AP\n"
        sampling_bytes = b"stratum,patient_pool_N\nsynthetic,1\n"
        (manifest_path.parent / "validation_inputs.csv").write_bytes(validation_bytes)
        (manifest_path.parent / "sampling_design_inputs.csv").write_bytes(sampling_bytes)
        manifest_path.write_text(
            json.dumps(
                {
                    "reference": {
                        "reference_label_source": {
                            "filename": "REVIEWED_REFERENCE_LABEL_SET.csv",
                            "path": "03_reference_standard/REVIEWED_REFERENCE_LABEL_SET.csv",
                            "sha256": digest,
                        },
                        "source_hashes": {"REVIEWED_REFERENCE_LABEL_SET.csv": digest},
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
            ),
            encoding="utf-8",
        )

        source = reference_label_source_from_manifest(manifest_path)

        self.assertEqual(source["filename"], "REVIEWED_REFERENCE_LABEL_SET.csv")
        self.assertEqual(source["path"], "03_reference_standard/REVIEWED_REFERENCE_LABEL_SET.csv")
        self.assertEqual(source["sha256"], digest)


if __name__ == "__main__":
    unittest.main()
