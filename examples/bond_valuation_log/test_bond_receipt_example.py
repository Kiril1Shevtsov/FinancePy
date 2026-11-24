"""A hand-calculated oracle and controlled negatives, not snapshot strings."""
import unittest
from dataclasses import replace

from bond_receipt_example import (
    Receipt, first_difference, make_receipt, planted_accrual_error, report,
)


class FixedCouponBondReceiptTest(unittest.TestCase):
    def setUp(self):
        self.actual = make_receipt()
        # Two remaining payments: 3 and 103. Zero rate gives 106 dirty.
        # 30E/360, Jan 15 -> Apr 15: 90/360 * 6 = 1.5 accrued.
        self.oracle = Receipt(
            (("2025-07-15", 3.0), ("2026-01-15", 103.0)), 1.5, 104.5, 106.0,
        )

    def test_financepy_matches_independent_oracle(self):
        self.assertEqual(first_difference(self.oracle, self.actual), "none")
        self.assertAlmostEqual(self.actual.clean + self.actual.accrued,
                               self.actual.dirty, places=10)

    def test_equal_dirty_price_does_not_hide_accrual_error(self):
        planted = planted_accrual_error(self.actual)
        self.assertEqual(planted.dirty, self.actual.dirty)
        self.assertAlmostEqual(planted.clean + planted.accrued,
                               planted.dirty, places=10)
        self.assertEqual(first_difference(self.oracle, planted), "accrual")
        self.assertIn("accrual", report(self.oracle, planted).to_markdown())

    def test_schedule_precedes_accrual_and_pricing(self):
        planted = planted_accrual_error(self.actual)
        planted = replace(planted, flows=(("2025-07-16", 3.0),) + planted.flows[1:])
        self.assertEqual(first_difference(self.oracle, planted), "schedule")
        self.assertEqual(first_difference(
            self.oracle, replace(self.actual, dirty=107.0)
        ), "pricing")


if __name__ == "__main__":
    unittest.main()
