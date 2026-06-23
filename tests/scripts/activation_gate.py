#!/usr/bin/env python3
"""Activation smoke gate for a single skill.

Runs the activation eval restricted to one skill's positives and fails if
recall.yes drops more than DROP_PP (10pp) below the skill's baseline.
Re-baseline by editing BASELINES_PCT after a fresh full activation run.

Usage: activation_gate.py --skill uipath-data-fabric
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Rounded recall.yes baseline (in %) per skill, measured 2026-06-17 over each
# skill's FULL positive set on claude-sonnet-4-6 via Bedrock — the same model
# and full-set measurement the gate itself runs, so baseline and gate stay
# directly comparable. Nearest 5%. The gate fails a skill whose recall.yes
# drops more than DROP_PP below its baseline. Re-baseline by re-running the
# full activation positives and updating the values here.
BASELINES_PCT: dict[str, int] = {
    "uipath-automation-discovery": 100,
    "uipath-data-fabric": 100,
    "uipath-troubleshoot": 100,
    "uipath-feedback": 100,
    "uipath-governance": 100,
    "uipath-ixp": 100,
    "uipath-mcp-servers": 100,
    "uipath-tasks": 100,
    "uipath-human-in-the-loop": 100,
    "uipath-rpa": 100,
    "uipath-test": 100,
    "uipath-platform": 100,
    "uipath-maestro-flow": 95,
    "uipath-maestro-bpmn": 95,
    "uipath-admin": 95,
    "uipath-review": 95,
    "uipath-planner": 95,
    "uipath-coded-apps": 90,
    "uipath-solution": 90,
    "uipath-agents": 90,
    "uipath-maestro-case": 90,
    "uipath-api-workflow": 90,
}

DROP_PP = 10


def _build_task_yaml(skill: str, dataset: Path) -> str:
    # Threshold gating lives in Python (see main) — keeping it out of the
    # YAML avoids two enforcement points with potentially different
    # comparison semantics at the boundary.
    return f"""\
task_id: skill-activation-gate-{skill}
description: Single-skill activation gate (positives only) for {skill}
tags: [activation, gate]

sandbox:
  driver: tempdir
  python: {{}}

dataset:
  paths:
    - {dataset}

initial_prompt: "${{row.prompt}}"

success_criteria:
  - type: skill_triggered
    description: "{skill} activation"
    skill_name: {skill}
    expected_skill: "${{row.expected_skill}}"
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    skill = parser.parse_args().skill

    if skill not in BASELINES_PCT:
        print(f"SKIP: no baseline for {skill!r}", file=sys.stderr)
        return 0

    baseline = BASELINES_PCT[skill]
    threshold_pct = baseline - DROP_PP
    threshold = threshold_pct / 100.0

    repo_root = Path(__file__).resolve().parents[2]
    dataset = (repo_root / "tests" / "tasks" / "activation" / f"{skill}.jsonl").resolve()
    if not dataset.is_file():
        print(f"ERROR: dataset {dataset} missing", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix=f"activation-gate-{skill}-") as tmp:
        tmp_path = Path(tmp)
        task_yaml = tmp_path / "gate.yaml"
        task_yaml.write_text(_build_task_yaml(skill, dataset), encoding="utf-8")
        run_dir = tmp_path / "run"

        result = subprocess.run(
            [
                "coder-eval", "run", str(task_yaml),
                "-e", "tests/experiments/activation.yaml",
                "-j", "4",
                "--run-dir", str(run_dir),
            ],
            cwd=repo_root, check=False,
        )
        # coder-eval exits non-zero whenever any individual task fails its
        # criteria. That's exactly the case DROP_PP is designed to absorb —
        # the threshold check below is the single source of truth. Only
        # treat the run as broken if suite.json never materialised.
        if result.returncode != 0:
            print(
                f"::notice::coder-eval exited with code {result.returncode} "
                f"(per-task failures expected; deferring to threshold check)",
                file=sys.stderr,
            )

        suite_json = run_dir / "default" / f"skill-activation-gate-{skill}" / "suite.json"
        if not suite_json.is_file():
            print(f"ERROR: {suite_json} missing", file=sys.stderr)
            return 2

        data = json.loads(suite_json.read_text(encoding="utf-8"))
        recall = next(
            (agg["metrics"]["recall.yes"]
             for agg in data.get("criterion_aggregates", [])
             if agg.get("criterion_type") == "skill_triggered"),
            None,
        )
        if recall is None:
            print("ERROR: recall.yes missing in suite.json", file=sys.stderr)
            return 2

        recall_pct = recall * 100
        if recall < threshold:
            print(
                f"::error::activation-gate {skill}: recall.yes "
                f"{recall_pct:.1f}% < {threshold_pct}% "
                f"(baseline {baseline} - {DROP_PP}pp)"
            )
            return 1
        print(
            f"::notice::activation-gate {skill}: PASS "
            f"({recall_pct:.1f}% >= {threshold_pct}%)"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
