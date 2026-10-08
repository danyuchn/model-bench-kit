"""Answer key (computed before any model ran): TWD 38,990 / USD 1,149.

Traps: ch_01 and ch_10 are Aug 31 in UTC but Sep 1 in Taipei (include);
ch_08 is Sep 30 in UTC but Oct 1 in Taipei (exclude); ch_06 failed and ch_09
pending (exclude); ch_05 partial refund; amounts are in 1/100 units.
"""
import re

from grade import last_line_with


def grade(text, out_dir):
    line = last_line_with(text, "TWD")
    vals = {float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", line)}
    ok = 38990.0 in vals and 1149.0 in vals
    utc_trap = 35990.0 in vals  # answered in UTC instead of Taipei time
    return float(ok), line.strip()[:70] + (" UTC-TRAP" if utc_trap else "")
