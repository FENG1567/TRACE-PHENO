import unittest
from pathlib import Path

from trace_pheno.validation import scan_public_tree, validate_json_files, validate_registry


ROOT = Path(__file__).resolve().parents[1]


class PublicPackageTests(unittest.TestCase):
    def test_registry_has_explicit_metric_semantics(self):
        self.assertEqual(validate_registry(ROOT / "results" / "manuscript_result_registry.csv"), [])

    def test_json_is_parseable(self):
        self.assertEqual(validate_json_files(ROOT / "configs"), [])
        self.assertEqual(validate_json_files(ROOT / "schemas"), [])

    def test_no_forbidden_public_content(self):
        self.assertEqual(scan_public_tree(ROOT), [])


if __name__ == "__main__":
    unittest.main()
