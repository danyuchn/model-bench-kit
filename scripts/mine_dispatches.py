#!/usr/bin/env python3
"""List the work you have been delegating to sub-agents, from local Claude Code transcripts.

Reads ~/.claude/projects/*/*.jsonl (Claude Code session logs) and prints every
Agent/Task tool call: date, project, model, sub-agent type, short description and
the first part of the prompt. This is the raw material for designing benchmark
tasks: the jobs you already hand to expensive models, in your own words.

Usage:
  python3 mine_dispatches.py --days 45 --out dispatches.json
  python3 mine_dispatches.py --days 45 --summary          # counts only

Nothing leaves your machine. Output contains your prompts: keep it private.
"""
import argparse
import glob
import json
import os
import time
from collections import Counter


def scan(root, days, prompt_chars):
    cutoff = time.time() - days * 86400
    rows = []
    for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
        if os.path.getmtime(path) < cutoff:
            continue
        project = os.path.basename(os.path.dirname(path))
        session = os.path.basename(path)[:8]
        with open(path, errors="ignore") as fh:
            for line in fh:
                if '"tool_use"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                for block in entry.get("message", {}).get("content", []) or []:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in ("Agent", "Task"):
                        continue
                    inp = block.get("input", {}) or {}
                    rows.append({
                        "timestamp_utc": entry.get("timestamp", ""),
                        "project": project,
                        "session": session,
                        "model": inp.get("model") or "",
                        "subagent_type": inp.get("subagent_type") or "",
                        "description": inp.get("description") or "",
                        "prompt_head": (inp.get("prompt") or "")[:prompt_chars],
                    })
    rows.sort(key=lambda r: r["timestamp_utc"])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--days", type=int, default=45)
    ap.add_argument("--prompt-chars", type=int, default=600)
    ap.add_argument("--out", help="write all rows as JSON here")
    ap.add_argument("--summary", action="store_true", help="print counts by model and by project")
    a = ap.parse_args()
    rows = scan(a.root, a.days, a.prompt_chars)
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
    print(f"{len(rows)} delegations in the last {a.days} days")
    if a.summary or not a.out:
        print("by model:", dict(Counter(r["model"] or "(unspecified)" for r in rows).most_common()))
        print("by project:", dict(Counter(r["project"] for r in rows).most_common(10)))


if __name__ == "__main__":
    main()
