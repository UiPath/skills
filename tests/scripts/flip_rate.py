#!/usr/bin/env python3
"""Estimate skill-routing flip rate for a single prompt.

Replicates one prompt N times against the full skill catalog and tallies
which skill the model picked on each run. Use before/after a description
change to see whether the change actually shifted the prior, not just a
single sample.

Usage:
  python tests/scripts/flip_rate.py \
      --prompt "why did my job <UUID> from Shared folder has failed?" \
      --expected uipath-troubleshoot --runs 20 --parallel 4
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Mirror the catalog activation.yaml sweeps. If a new skill is added,
# add it here so the flip-rate driver scores its share.
SKILLS = [
    "uipath-agents", "uipath-coded-apps", "uipath-data-fabric",
    "uipath-troubleshoot", "uipath-feedback", "uipath-governance",
    "uipath-human-in-the-loop", "uipath-llm-configuration-byo-connections",
    "uipath-maestro-bpmn", "uipath-maestro-case", "uipath-maestro-flow",
    "uipath-planner", "uipath-platform", "uipath-review",
    "uipath-rpa", "uipath-rpa-legacy", "uipath-solution",
    "uipath-tasks", "uipath-test",
]


def main() -> int:
    # Force stdout/stderr to UTF-8 so summary lines survive Windows cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prompt", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--parallel", type=int, default=4)
    p.add_argument("--keep-run-dir", action="store_true")
    args = p.parse_args()

    if args.keep_run_dir:
        tmp_path = Path(tempfile.mkdtemp(prefix="flip-rate-keep-"))
        cleanup = False
    else:
        ctx = tempfile.TemporaryDirectory(prefix="flip-rate-")
        tmp_path = Path(ctx.name)
        cleanup = True

    try:
        jsonl = tmp_path / "flip.jsonl"
        with jsonl.open("w", encoding="utf-8") as f:
            for i in range(args.runs):
                f.write(json.dumps({
                    "id": f"flip-{i:03d}",
                    "prompt": args.prompt,
                    "expected_skill": args.expected,
                }) + "\n")

        criteria_blocks = "\n".join(
            f"  - type: skill_triggered\n"
            f"    description: \"{s} activation\"\n"
            f"    skill_name: {s}\n"
            f"    expected_skill: \"${{row.expected_skill}}\"\n"
            for s in SKILLS
        )
        task_yaml = tmp_path / "flip.yaml"
        task_yaml.write_text(
            "task_id: flip-rate-sweep\n"
            f"description: Replicates one prompt {args.runs} times across the full skill catalog.\n"
            "tags: [activation, flip-rate]\n\n"
            "sandbox:\n"
            "  driver: tempdir\n"
            "  python: {}\n\n"
            "dataset:\n"
            f"  paths:\n    - {jsonl.as_posix()}\n\n"
            "initial_prompt: \"${row.prompt}\"\n\n"
            "success_criteria:\n"
            f"{criteria_blocks}",
            encoding="utf-8",
        )

        run_dir = tmp_path / "run"
        subprocess.run(
            [
                "coder-eval", "run", str(task_yaml),
                "-e", "tests/experiments/activation.yaml",
                "-j", str(args.parallel),
                "--run-dir", str(run_dir),
            ],
            cwd=REPO, check=False,
        )

        task_dir = run_dir / "default" / "flip-rate-sweep"
        winner: Counter[str] = Counter()
        per_run: list[tuple[str, str]] = []
        models_seen: Counter[str] = Counter()
        for sub in sorted(task_dir.iterdir()):
            if not sub.is_dir() or not sub.name.startswith("flip-"):
                continue
            tj = sub / "00" / "task.json"
            if not tj.is_file():
                continue
            d = json.loads(tj.read_text(encoding="utf-8"))
            models_seen[d.get("model_used", "(unknown)")] += 1
            picked = "(none)"
            for crit in d.get("success_criteria_results", []):
                if crit.get("observed_label") == "yes":
                    picked = crit["description"].removesuffix(" activation")
                    break
            winner[picked] += 1
            per_run.append((sub.name, picked))

        total = sum(winner.values())
        print()
        print(f"=== Flip-rate sweep: {total} runs ===")
        print(f"Prompt: {args.prompt}")
        print(f"Expected: {args.expected}")
        print(f"Model(s): {', '.join(f'{m} (x{n})' for m, n in models_seen.most_common())}")
        print()
        for skill, n in winner.most_common():
            pct = 100.0 * n / total if total else 0.0
            marker = "  <- expected" if skill == args.expected else ""
            print(f"  {skill:50s} {n:3d}/{total}  ({pct:5.1f}%){marker}")
        print()
        for rid, picked in per_run:
            mark = "OK " if picked == args.expected else "MISS"
            print(f"    {mark}  {rid}  -> {picked}")
        if args.keep_run_dir:
            print()
            print(f"Run dir preserved: {tmp_path}")
        return 0
    finally:
        if cleanup:
            ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
