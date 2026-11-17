import unittest

from trace_pheno.equivalence import p3_p4_equivalence


class EquivalenceTests(unittest.TestCase):
    def test_p3_p4_complete_binary_equivalence(self):
        result = p3_p4_equivalence()
        self.assertTrue(result["equivalent"])
        self.assertEqual(len(result["truth_table"]), 8)


if __name__ == "__main__":
    unittest.main()
