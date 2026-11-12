import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from low_stock import filter_low_stock  # noqa: E402


def variant(qty, status="ACTIVE", tracked=True, title="Default", product="Bed"):
    return {"title": title, "sku": "SKU", "inventoryQuantity": qty,
            "inventoryItem": {"tracked": tracked},
            "product": {"title": product, "status": status}}


class FilterTests(unittest.TestCase):
    def test_threshold_and_sorting(self):
        rows = filter_low_stock([variant(10), variant(3, product="B"), variant(0, product="A")], 5)
        self.assertEqual([r["quantity"] for r in rows], [0, 3])

    def test_skips_drafts_by_default(self):
        self.assertEqual(filter_low_stock([variant(1, status="DRAFT")], 5), [])
        self.assertEqual(len(filter_low_stock([variant(1, status="DRAFT")], 5, include_drafts=True)), 1)

    def test_skips_untracked_by_default(self):
        self.assertEqual(filter_low_stock([variant(0, tracked=False)], 5), [])
        self.assertEqual(len(filter_low_stock([variant(0, tracked=False)], 5, include_untracked=True)), 1)

    def test_negative_stock_included(self):
        self.assertEqual(filter_low_stock([variant(-2)], 0)[0]["quantity"], -2)


if __name__ == "__main__":
    unittest.main()
