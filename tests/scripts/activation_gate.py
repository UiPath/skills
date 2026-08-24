#!/usr/bin/env python3
"""Activation smoke gate for a single skill.

Runs the activation eval restricted to one skill's positives and fails if
recall.yes drops more than DROP_PP (10pp) below the skill's baseline.
Re-baseline by editing BASELINES_PCT after a fresh full activation run.

Usage: activation_gate.py --skill uipath-platform
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# The gate's agent model. Passed explicitly rather than pinned in
# experiments/activation.yaml so one variable moves every eval entry point in this
# repo, and so the model the baselines below were measured against is visible at the
# call site. No default: the baselines are model-specific, so silently gating a
# different model than the one they were measured on would report a meaningless
# verdict. NOT $BEDROCK_MODEL: that is the evaluation-side model (llm_judge + the
# simulated user), which must not move with the agent under test.
AGENT_MODEL = os.environ.get("AGENT_MODEL", "").strip()

# Rounded recall.yes baseline (in %) per skill, measured 2026-06-17 over each
# skill's FULL positive set on claude-sonnet-4-6 via Bedrock at max_turns: 1 —
# the same model and full-set measurement the gate itself runs. The gate task
# pins run_limits.max_turns: 1 (task layer overrides the experiment's 3 via
# per-key field-merge) so baseline and gate stay directly comparable; at 3
# turns engagement is a monotone union over the trajectory, recall could only
# rise, and every baseline would become an easier floor. Nearest 5%. The gate
# fails a skill whose recall.yes drops more than DROP_PP below its baseline.
# Re-baseline (at max_turns: 1) after a fresh full activation run.
BASELINES_PCT: dict[str, int] = {
    "uipath-automation-discovery": 100,
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
    # uipath-planner re-measured 2026-08-07 on the current gate model
    # (claude-sonnet-5). The prior 95% figure predates the #2132 model
    # retarget, and no PR between the retarget and this measurement changed
    # planner frontmatter, so the gate never ran on the new model. Measured
    # recall over the full positive set: main's own unchanged frontmatter
    # 65.9% and 59.3% (two dispatches: actions/runs/31219477420,
    # actions/runs/31220789082); the planner-sole-sdd-author branch 59.3%,
    # 52.7%, 51.6%. Run-to-run spread is ~7pp on this skill's ambiguous
    # positives, so 60 sits between the two arms' means; DROP_PP absorbs the
    # spread. Re-baseline again after the next full activation run.
    "uipath-planner": 60,
    "uipath-coded-apps": 90,
    "uipath-solution": 90,
    "uipath-agents": 90,
    "uipath-maestro-case": 90,
    "uipath-api-workflow": 90,
    "uipath-functions": 95,
}

DROP_PP = 10


def _build_task_yaml(skill: str, dataset: Path) -> str:
    # Threshold gating lives in Python (see main) — keeping it out of the
    # YAML avoids two enforcement points with potentially different
    # comparison semantics at the boundary.
    #
    # stop_early: {{on_pass: stop}} is the coder-eval 0.9.5 arming — 0.9.5
    # removed the stop_when field (breaking change); per-criterion stop_early
    # blocks replace it, the same migration #2504 applied to activation.yaml.
    # Gate rows are all positives, so pass-stop arms: the run
    # ends the moment {skill} engages, with the verdict a full run would
    # have produced (any-engagement latch is monotonic), and a recall miss
    # never fires a live event so it still runs to the cap. With a single
    # positive criterion and no distractors, early stop cannot change
    # recall.yes — only cost.
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

# Baselines were measured at max_turns: 1 — pin it here (task layer wins the
# per-key merge over the experiment's 3) so the gate measures the same thing.
# Early stop arms per-criterion via the stop_early block below (0.9.5 shape).
run_limits:
  max_turns: 1

initial_prompt: "${{row.prompt}}"

success_criteria:
  - type: skill_triggered
    description: "{skill} activation"
    skill_name: {skill}
    expected_skill: "${{row.expected_skill}}"
    stop_early:
      on_pass: stop
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    skill = parser.parse_args().skill

    if not AGENT_MODEL:
        print("ERROR: AGENT_MODEL is unset — set the CLAUDE_CODE_MODEL repo variable", file=sys.stderr)
        return 2

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
                "--model", AGENT_MODEL,
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
        metrics = next(
            (agg["metrics"]
             for agg in data.get("criterion_aggregates", [])
             if agg.get("criterion_type") == "skill_triggered"),
            None,
        )
        recall = metrics.get("recall.yes") if metrics else None
        if recall is None:
            print("ERROR: recall.yes missing in suite.json", file=sys.stderr)
            return 2

        # A timed-out/errored row has no criterion result and is EXCLUDED from
        # recall's denominator, not counted as a miss — recall alone can look
        # fine on a partial run. Require every row to have been scored.
        completion = metrics.get("completion_rate")
        if completion is not None and completion < 1.0:
            print(
                f"::error::activation-gate {skill}: completion_rate "
                f"{completion * 100:.1f}% < 100% — rows dropped from the "
                f"denominator (timeout/error); recall.yes is not trustworthy"
            )
            return 1

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
