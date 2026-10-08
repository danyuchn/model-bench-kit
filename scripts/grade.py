#!/usr/bin/env python3
"""Grade benchmark runs with per-task graders and print a comparison table.

Usage:
  python3 grade.py bench.json [-v]

Each task T has a grader file <graders_dir>/T.py defining
    grade(text: str, out_dir: pathlib.Path) -> tuple[float, str]
returning a score in 0..1 and a short detail string a human can audit.
`text` is ALL assistant text of the run, not only the final message: a Stop hook
can force an extra turn whose final message just says "answer unchanged", and
grading only that message silently scores a correct answer as zero.
"""
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def full_text(result, out_dir):
    sid = result.get("session_id")
    proj = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(out_dir))
    f = proj / f"{sid}.jsonl"
    if not sid or not f.exists():
        return result.get("result") or ""
    parts = []
    for line in f.open(errors="ignore"):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c["text"])
    return "\n".join(parts) or (result.get("result") or "")


def last_line_with(text, label):
    """Last line containing label: use it to read a final-answer line the prompt asked for."""
    for line in reversed(text.splitlines()):
        if label in line:
            return line
    return ""


def load_grader(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grade


def main():
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    base = cfg_path.parent
    work = base / cfg.get("work_dir", "runs")
    graders = base / cfg.get("graders_dir", "graders")
    sys.path.insert(0, str(Path(__file__).parent))  # graders can `from grade import last_line_with`
    cache = {}
    rows = []
    for f in sorted((work / "results").glob("*.json")):
        d = json.loads(f.read_text())
        job = d.get("_job")
        if not job:
            continue
        task = job["task"]
        out = Path(d["_out"]) if d.get("_out") else (work / "out" / f.stem).resolve()
        if task not in cache:
            gp = graders / f"{task}.py"
            cache[task] = load_grader(gp) if gp.exists() else None
        if d.get("is_error"):
            score, det = 0.0, "ERROR " + str(d.get("result", ""))[:60]
        elif cache[task] is None:
            score, det = 0.0, "no grader"
        else:
            try:
                score, det = cache[task](full_text(d, out), out)
            except Exception as e:  # a crashing grader must be visible, not a silent zero
                score, det = 0.0, f"GRADER ERROR {e}"
        denials = len(d.get("permission_denials") or [])
        rows.append({"task": task, "cfg": f"{job['model']}-{job['effort']}", "rep": job["rep"],
                     "score": round(score, 3), "cost": d.get("total_cost_usd") or 0, "turns": d.get("num_turns"),
                     "wall": d.get("_wall_s") or 0, "denials": denials, "detail": det})
    (work / "graded.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    if "-v" in sys.argv:
        for r in rows:
            flag = f" DENIED x{r['denials']}" if r["denials"] else ""
            print(f"{r['task']:4} {r['cfg']:16} r{r['rep']:<3} {r['score']:.2f} ${r['cost']:.3f} "
                  f"t={r['turns']} {r['wall']}s{flag} | {r['detail']}")
    agg = defaultdict(list)
    for r in rows:
        agg[(r["task"], r["cfg"])].append(r)
    print(f"\n{'task':5} {'config':17} n  mean  min   $/run   s/run")
    for (task, c), rs in sorted(agg.items()):
        n = len(rs)
        print(f"{task:5} {c:17} {n}  {sum(r['score'] for r in rs)/n:.2f}  {min(r['score'] for r in rs):.2f}  "
              f"{sum(r['cost'] for r in rs)/n:6.3f}  {sum(r['wall'] for r in rs)/n:6.0f}")


if __name__ == "__main__":
    main()
