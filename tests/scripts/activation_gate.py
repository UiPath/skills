#!/usr/bin/env python3
"""Activation smoke gate for a single skill.

Runs the activation eval restricted to one skill's positive prompts and fails
if recall.yes drops more than 15pp below its baseline. Baselines are hardcoded
from the 2026-05-08 full activation run; see activation-eval-findings-2026-05-08
in Downloads for provenance.

Scope (deliberately narrow):

  * Only runs that one skill's positives jsonl (~50 prompts).
  * Only evaluates that one skill's `skill_triggered` criterion.
  * Does NOT touch the shared negatives or other skills' prompts.

Re-baseline by replacing BASELINES_PCT after a fresh full activation run.

Usage:
    activation_gate.py --skill uipath-data-fabric
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Rounded recall.yes baseline (in %) per skill, from the 2026-05-08 full
# activation run (n ~= 50 positives per skill). Rounded to the nearest 5%.
# Skills with no activation test set (uipath-admin, uipath-ixp) are omitted
# and will produce a SKIP at runtime.
BASELINES_PCT: dict[str, int] = {
    "uipath-feedback": 90,
    "uipath-data-fabric": 90,
    "uipath-interact": 90,
    "uipath-planner": 90,
    "uipath-tasks": 85,
    "uipath-governance": 85,
    "uipath-rpa-legacy": 75,
    "uipath-platform": 70,
    "uipath-maestro-flow": 70,
    "uipath-human-in-the-loop": 70,
    "uipath-test": 70,
    "uipath-rpa": 70,
    "uipath-diagnostics": 70,
    "uipath-maestro-bpmn": 60,
    "uipath-coded-apps": 60,
    "uipath-llm-configuration-byo-connections": 60,
    "uipath-agents": 55,
    "uipath-solution-design": 50,
    "uipath-maestro-case": 45,
    "uipath-review": 20,
}

# Hard-fail threshold: actual recall.yes must stay within this many pp of the
# baseline. 15pp is just above the n=50 binomial noise floor (~2σ at p≈0.7);
# smaller drops fall into noise.
DROP_PP = 15


def _build_task_yaml(skill: str, dataset_path: Path, threshold: float) -> str:
    return f"""\
task_id: skill-activation-gate-{skill}
description: Single-skill activation gate (positives only) for {skill}
tags: [activation, gate]

sandbox:
  driver: tempdir
  python: {{}}

dataset:
  paths:
    - {dataset_path}

initial_prompt: "${{row.prompt}}"

success_criteria:
  - type: skill_triggered
    description: "{skill} activation"
    skill_name: {skill}
    expected_skill: "${{row.expected_skill}}"
    suite_thresholds: {{recall.yes: {threshold:.4f}}}
"""


def _find_suite_json(run_dir: Path) -> Path | None:
    candidates = sorted(run_dir.rglob("suite.json"))
    return candidates[-1] if candidates else None


def _extract_recall_yes(suite_json: Path, skill: str) -> tuple[float | None, bool | None]:
    """Return (recall_yes, threshold_passed) from suite.json, or (None, None)."""
    data = json.loads(suite_json.read_text(encoding="utf-8"))
    aggregates = data.get("criterion_aggregates") or []
    for agg in aggregates:
        if agg.get("criterion_type") != "skill_triggered":
            continue
        recall = (agg.get("metrics") or {}).get("recall.yes")
        passed = agg.get("passed")
        if recall is not None:
            return float(recall), bool(passed) if passed is not None else None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="Skill name, e.g. uipath-data-fabric")
    parser.add_argument(
        "--parallelism", type=int,
        default=int(os.environ.get("TASK_PARALLELISM", "4")),
    )
    parser.add_argument(
        "--experiment",
        default="tests/experiments/activation.yaml",
        help="Experiment yaml relative to repo root",
    )
    parser.add_argument(
        "--run-dir", default=None,
        help="Override run output dir (default: a tempdir under TMPDIR)",
    )
    args = parser.parse_args()

    skill = args.skill
    if skill not in BASELINES_PCT:
        print(
            f"SKIP: no activation-gate baseline for {skill!r}. "
            f"Allowed: {sorted(BASELINES_PCT)}",
            file=sys.stderr,
        )
        return 0

    baseline_pct = BASELINES_PCT[skill]
    threshold_pct = baseline_pct - DROP_PP
    threshold = threshold_pct / 100.0

    repo_root = Path(__file__).resolve().parents[2]
    dataset = (repo_root / "tests" / "tasks" / "activation" / f"{skill}.jsonl").resolve()
    if not dataset.is_file():
        print(f"ERROR: dataset {dataset} not found", file=sys.stderr)
        return 1

    row_count = sum(1 for _ in dataset.open(encoding="utf-8"))

    print(
        f"== activation-gate: {skill} ==\n"
        f"  baseline (rounded): {baseline_pct}%\n"
        f"  drop allowed:       {DROP_PP}pp\n"
        f"  fail threshold:     recall.yes < {threshold_pct}% ({threshold:.2f})\n"
        f"  dataset:            {dataset.name} ({row_count} rows)\n",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix=f"activation-gate-{skill}-") as tmp:
        tmp_path = Path(tmp)
        task_yaml = tmp_path / f"gate-{skill}.yaml"
        task_yaml.write_text(_build_task_yaml(skill, dataset, threshold), encoding="utf-8")

        run_dir = Path(args.run_dir) if args.run_dir else (tmp_path / "run")
        run_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "coder-eval", "run", str(task_yaml),
            "-e", args.experiment,
            "-j", str(args.parallelism),
            "--run-dir", str(run_dir),
            "--preserve",
        ]
        cwd = repo_root
        print(f"$ {' '.join(cmd)}  (cwd={cwd})", flush=True)
        proc = subprocess.run(cmd, cwd=cwd, check=False)

        suite_json = _find_suite_json(run_dir)
        if suite_json is None:
            print(
                f"ERROR: no suite.json under {run_dir} "
                f"(coder-eval exit={proc.returncode})",
                file=sys.stderr,
            )
            return 2

        recall, passed = _extract_recall_yes(suite_json, skill)
        if recall is None:
            print(
                f"ERROR: skill_triggered aggregate missing in {suite_json}",
                file=sys.stderr,
            )
            return 2

        recall_pct = recall * 100
        verdict = "PASS" if recall >= threshold else "FAIL"
        print(
            f"\n== result ==\n"
            f"  skill:       {skill}\n"
            f"  rows:        {row_count}\n"
            f"  recall.yes:  {recall_pct:.1f}%  "
            f"(baseline {baseline_pct}%, fail < {threshold_pct}%)\n"
            f"  verdict:     {verdict}\n"
            f"  suite.json:  {suite_json}\n",
            flush=True,
        )

        if recall < threshold:
            print(
                f"::error::activation-gate {skill}: recall.yes "
                f"{recall_pct:.1f}% < {threshold_pct}% "
                f"(baseline {baseline_pct} - {DROP_PP}pp)",
                flush=True,
            )
            return 1

        print(
            f"::notice::activation-gate {skill}: PASS "
            f"({recall_pct:.1f}% >= {threshold_pct}%)",
            flush=True,
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
