#!/usr/bin/env python3
"""Resumable benchmark runner for Claude Code headless mode (`claude -p`).

Usage:
  python3 runner.py bench.json jobs.txt

bench.json (one per benchmark):
  {
    "tasks_dir": "tasks",            # <TASK>.txt prompt files; {{OUT}} -> the run's output dir,
                                     # {{BENCH}} -> this bench.json's folder (for fixtures/)
    "work_dir": "runs",              # results/ and out/ are created here
    "workers": 2,                    # keep this small: each worker is a full agent session
    "budget_usd_per_run": 4,
    "timeout_s": 1500,
    "compute_tasks": ["T5", "T7"]    # tasks allowed to run python3 and write inside {{OUT}}
  }

jobs.txt: one job per line, `TASK MODEL EFFORT REP`, e.g. `T3 haiku medium 0`.
Finished jobs write results/<TASK>__<MODEL>-<EFFORT>__r<REP>.json and are skipped on re-run,
so the same command resumes after a crash. REP values starting with "p" add `mkdir` to the
compute allow-list (use them for a permission-relaxed re-run).

Every run is started in its own empty output directory, never inside a real project:
project-level hooks and instructions would otherwise act on the model under test.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main():
    cfg_path, jobs_path = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(cfg_path.read_text())
    base = cfg_path.parent
    tasks_dir = base / cfg.get("tasks_dir", "tasks")
    work = base / cfg.get("work_dir", "runs")
    (work / "results").mkdir(parents=True, exist_ok=True)
    log_path = work / "runner.log"
    compute = set(cfg.get("compute_tasks", []))

    def log(msg):
        with log_path.open("a") as fh:
            fh.write(time.strftime("%H:%M:%S ") + msg + "\n")

    def run(job):
        task, model, effort, rep = job
        tag = f"{task}__{model}-{effort}__r{rep}"
        res = work / "results" / f"{tag}.json"
        if res.exists():
            return
        out = (work / "out" / tag).resolve()
        out.mkdir(parents=True, exist_ok=True)
        prompt = ((tasks_dir / f"{task}.txt").read_text()
                  .replace("{{OUT}}", str(out)).replace("{{BENCH}}", str(base.resolve())))
        cmd = ["claude", "-p", "--model", model, "--effort", effort, "--output-format", "json",
               "--permission-mode", "dontAsk", "--max-budget-usd", str(cfg.get("budget_usd_per_run", 4))]
        if task in compute:
            extra = ["Bash(mkdir:*)"] if str(rep).startswith("p") else []
            cmd += ["--allowedTools", "Read", "Glob", "Grep", "Bash(python3:*)", *extra,
                    f"Write(/{out}/**)", f"Edit(/{out}/**)", "--disallowedTools", "Agent", "Task"]
        else:
            cmd += ["--allowedTools", "Read", "Glob", "Grep",
                    "--disallowedTools", "Bash", "Edit", "Write", "Agent", "Task"]
        log(f"start {tag}")
        t0 = time.time()
        try:
            p = subprocess.run(cmd + ["--", prompt], cwd=out, capture_output=True, text=True,
                               timeout=cfg.get("timeout_s", 1500))
            raw = p.stdout
        except subprocess.TimeoutExpired:
            raw = json.dumps({"is_error": True, "result": "TIMEOUT"})
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"is_error": True, "result": raw[-2000:]}
        data["_wall_s"] = round(time.time() - t0, 1)
        data["_job"] = {"task": task, "model": model, "effort": effort, "rep": rep}
        res.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        log(f"done  {tag} cost={data.get('total_cost_usd')} turns={data.get('num_turns')} wall={data['_wall_s']}")

    jobs = [tuple(l.split()) for l in jobs_path.read_text().splitlines() if l.strip() and not l.startswith("#")]
    log(f"jobs={len(jobs)}")
    with ThreadPoolExecutor(cfg.get("workers", 2)) as ex:
        list(ex.map(run, jobs))
    log("ALL DONE")


if __name__ == "__main__":
    main()
