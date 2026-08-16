import unittest

from trace_pheno.aki_demo import creatinine_rule, urine_rule


class AkiDemoTests(unittest.TestCase):
    def test_delta_48h(self):
        self.assertEqual(creatinine_rule([0.9, 1.1, 1.3], [0, 12, 30]), "delta_48h")

    def test_ratio_7d(self):
        self.assertEqual(creatinine_rule([1.0, 1.0, 1.6], [0, 96, 150]), "ratio_7d")

    def test_urine_and_missing_weight(self):
        self.assertEqual(urine_rule([20] * 6, 70), "urine_6h")
        self.assertEqual(urine_rule([20] * 6, None), "missing_normalizer")


if __name__ == "__main__":
    unittest.main()
