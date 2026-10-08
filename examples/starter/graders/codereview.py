"""Answer key: 3 planted bugs in check_invoices.py.

1. rows[:-1] silently skips the last line item.
2. `abs(total - stated) < 0.01` is inverted: it flags matching invoices and passes broken ones.
3. sys.exit(0) always, while the docstring promises exit 1 on failure (the gate never closes).
Keyword matching is a first pass; read any run scoring below 1 before trusting the number.
"""
import re

CHECKS = {
    "skips-last-row": r"\[:-1\]|最後一(列|行|筆)|last (row|line)",
    "inverted-compare": r"<\s*0\.01|反了|inverted|相反|顛倒",
    "exit-always-0": r"sys\.exit\(0\)|exit code|離開碼|exit\s*1",
}


def grade(text, out_dir):
    hit = [k for k, rx in CHECKS.items() if re.search(rx, text, re.I)]
    return len(hit) / len(CHECKS), f"hit={hit}"
