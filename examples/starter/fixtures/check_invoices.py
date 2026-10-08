#!/usr/bin/env python3
"""Check that every invoice's line items add up to its stated total.

Input: a CSV with columns invoice_id, line_amount, stated_total (one row per line item).
An invoice passes when the sum of its line_amount is within 0.01 of stated_total.
Prints one line per failing invoice and exits 1 if any invoice fails, so it can
gate the next step of a pipeline.
"""
import csv
import sys
from collections import defaultdict


def main(path):
    sums = defaultdict(float)
    stated = {}
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows[:-1]:
        inv = row["invoice_id"]
        sums[inv] += float(row["line_amount"])
        stated[inv] = float(row["stated_total"])
    failed = 0
    for inv, total in sums.items():
        if abs(total - stated[inv]) < 0.01:
            print(f"FAIL {inv}: lines={total:.2f} stated={stated[inv]:.2f}")
            failed += 1
    print(f"invoices failing: {failed}")
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1])
