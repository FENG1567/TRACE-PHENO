import unittest

from trace_pheno.numeric import parse_enzyme_result, parse_number


class NumericTests(unittest.TestCase):
    def test_scientific_notation(self):
        self.assertEqual(parse_number("1.8e2 IU/L"), 180.0)

    def test_iu_l_variants(self):
        for unit in ("IU/L", "U/L", "Units/L", "units / l"):
            result = parse_enzyme_result("180", "60", unit)
            self.assertEqual(result.status, "computable")
            self.assertEqual(result.multiple_uln, 3.0)

    def test_missing_uln_is_not_negative(self):
        result = parse_enzyme_result(500, None, "IU/L")
        self.assertEqual(result.status, "missing_uln")
        self.assertIsNone(result.multiple_uln)


if __name__ == "__main__":
    unittest.main()
