import csv
import unittest
from pathlib import Path

from trace_pheno.phenotypes import evaluate_ap_case, is_ap_icd


ROOT = Path(__file__).resolve().parents[1]


class PhenotypeTests(unittest.TestCase):
    def cases(self):
        with (ROOT / "data" / "synthetic" / "AP_synthetic_cases.csv").open(encoding="utf-8-sig", newline="") as handle:
            return {row["case_id"]: row for row in csv.DictReader(handle)}

    def test_icd_value_set(self):
        self.assertTrue(is_ap_icd("577.0"))
        self.assertTrue(is_ap_icd("K85.9"))
        self.assertFalse(is_ap_icd("K86.0"))

    def test_primary_and_secondary(self):
        cases = self.cases()
        self.assertTrue(evaluate_ap_case(cases["S-AP-01"])["P1"].positive)
        self.assertFalse(evaluate_ap_case(cases["S-AP-02"])["P1"].positive)

    def test_exact_uln_boundary(self):
        cases = self.cases()
        self.assertTrue(evaluate_ap_case(cases["S-AP-04"])["P2"].positive)
        self.assertFalse(evaluate_ap_case(cases["S-AP-05"])["P2"].positive)

    def test_missing_uln_not_computable(self):
        result = evaluate_ap_case(self.cases()["S-AP-07"])["P2"]
        self.assertIsNone(result.positive)
        self.assertEqual(result.status, "not_computable")

    def test_no_radiology_number_as_icd(self):
        self.assertFalse(evaluate_ap_case(self.cases()["S-AP-13"])["P0"].positive)


if __name__ == "__main__":
    unittest.main()
