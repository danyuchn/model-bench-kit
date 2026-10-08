"""Answer key: 5 planted violations.

R3 1.2 hours (fact sheet says 2.1); R1 北辰物流; R4 保證...零遺漏; R2 K-12 專案卡; R1 禾豐食品.
Scores recall only. Extra findings are NOT penalised automatically: read them, because a
strong model often finds defensible extras (e.g. the promise sentence also contains numbers
that are not in the fact sheet). Count a false positive only after reading it.
"""
import re

PLANTED = {"1.2 hours": "1.2", "北辰物流": "北辰", "guarantee": "保證", "K-12": "K-12", "禾豐食品": "禾豐"}


def grade(text, out_dir):
    hit = [k for k, v in PLANTED.items() if v in text]
    m = re.search(r"違規總數[:：]\s*\**\s*(\d+)", text)
    n = int(m.group(1)) if m else -1
    return len(hit) / len(PLANTED), f"hit={hit} reported_total={n}"
