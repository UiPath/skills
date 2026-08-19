#!/usr/bin/env python3
"""Assert a coder-eval run measured what it claims, BEFORE anyone reads its scores.

Why this exists
---------------
A coder-eval run can complete, report per-task scores, and mean nothing. Observed
failures, all of which produced plausible numbers:

  * the skill under test was never installed — the run silently fell back to
    coder-eval's built-in default experiment, which has no `plugins:` block, so the
    agent ran with no skill at all and every skill-contract criterion failed
  * the model never executed — a provider error (expired credit, auth) ends the
    dialog after ~2 turns while the orchestrator still writes a finished task.json
    with a score
  * the judge had no transport — `llm_judge` scores 0.0 with
    "(judge transport unconfigured)", so every task is FAILURE regardless of merit

Each of those is indistinguishable from a real regression if you read only the
score. This gate makes them loud. Run it on a run directory before quoting any
number from it.

Usage
-----
    python3 scripts/check-eval-run.py RUN_DIR [--expect-experiment NAME]
                                              [--min-output-tokens N] [--json]

    # typical: the repo's own experiment must have been used
    python3 scripts/check-eval-run.py tests/runs/my-run --expect-experiment skill-tests-default

Exit 0 when every replicate is trustworthy, 1 otherwise. Says nothing about whether
the skill is correct — only whether the run is evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

JUDGE_UNCONFIGURED = "judge transport unconfigured"


def replicate_findings(task_json: pathlib.Path, min_output_tokens: int, regrade: bool = False) -> list[str]:
    """Reasons this replicate is not evidence. Empty list == trustworthy."""
    out: list[str] = []
    try:
        t = json.loads(task_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"unreadable task.json: {exc}"]

    # A `coder-eval evaluate` re-grade runs NO agent: there is no plugin install,
    # no token usage and no experiment report, so asserting those here would fail
    # every re-grade — the cheapest and most useful path. Only judge reachability
    # and the criteria themselves are meaningful in that mode.
    if regrade:
        for crit in t.get("success_criteria_results") or []:
            if JUDGE_UNCONFIGURED in str(crit.get("details", "")):
                out.append(
                    "llm_judge scored 0.0 with no judge transport — this re-grade's "
                    "pass/fail is not about the skill. Configure ANTHROPIC_API_KEY or Bedrock, "
                    "or use an agent_judge criterion, which runs on the local CLI login."
                )
                break
        return out

    agent_cfg = t.get("agent_config") or {}
    if not agent_cfg.get("plugins"):
        out.append(
            "no plugin loaded — agent_config.plugins is empty, so the skill under "
            "test was never installed (usually the built-in default experiment)"
        )

    # "Did the model execute?" is measured by output tokens, NOT by turn count.
    # Turn count is agent-dependent and misleading: codex reports
    # total_assistant_turns == 1 on fully successful runs and 2 on runs that died
    # on a provider error, so any turn threshold is near-inverted for it. Token
    # usage is absent entirely when the provider refused.
    usage = t.get("total_token_usage") or {}
    produced = usage.get("output_tokens")
    if not produced:
        turns = t.get("total_assistant_turns")
        out.append(
            "the model produced no output — total_token_usage is empty "
            f"(turns={turns}, agent={t.get('agent_type')}). Usually a provider error "
            "(expired credit, auth); check conversation.log"
        )
    elif min_output_tokens > 0 and produced < min_output_tokens:
        out.append(f"only {produced} output token(s) — suspiciously little work")

    for crit in t.get("success_criteria_results") or []:
        if JUDGE_UNCONFIGURED in str(crit.get("details", "")):
            out.append(
                "llm_judge scored 0.0 with no judge transport — this run's pass/fail "
                "is not about the skill. Configure ANTHROPIC_API_KEY or Bedrock, or use an "
                "agent_judge criterion, which runs on the local CLI login."
            )
            break

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=pathlib.Path)
    ap.add_argument("--expect-experiment", default=None,
                    help="fail unless the run's experiment report names this experiment")
    ap.add_argument("--min-output-tokens", type=int, default=1,
                    help="minimum model output tokens for a replicate to count (default 1)")
    ap.add_argument("--regrade", action="store_true",
                    help="the run came from `coder-eval evaluate` (no agent executed): "
                         "skip plugin/token/experiment assertions")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    run_dir: pathlib.Path = args.run_dir
    if not run_dir.is_dir():
        print(f"FAIL: no such run directory: {run_dir}", file=sys.stderr)
        return 1

    report: dict = {"run_dir": str(run_dir), "experiment": None, "replicates": [], "run_level": []}

    exp_md = run_dir / "experiment.md"
    if args.regrade:
        report["experiment"] = "(re-grade — no experiment)"
    elif exp_md.is_file():
        content = exp_md.read_text(encoding="utf-8")
        first = content.splitlines()[0] if content else ""
        name = first.split(":", 1)[-1].strip() if ":" in first else first.strip()
        report["experiment"] = name
        if args.expect_experiment and name != args.expect_experiment:
            report["run_level"].append(
                f"experiment is {name!r}, expected {args.expect_experiment!r} — a "
                "silent fallback to a different experiment changes what was measured"
            )
    else:
        report["run_level"].append(
            "no experiment.md — cannot confirm which experiment ran "
            "(pass --regrade if this came from `coder-eval evaluate`)"
        )

    task_jsons = sorted(run_dir.rglob("task.json"))
    if not task_jsons:
        report["run_level"].append("no task.json found — the run produced no replicates")

    bad = 0
    for tj in task_jsons:
        findings = replicate_findings(tj, args.min_output_tokens, regrade=args.regrade)
        rel = tj.relative_to(run_dir).parent
        report["replicates"].append({"replicate": str(rel), "findings": findings})
        bad += bool(findings)

    total = len(task_jsons)
    ok = total - bad
    report["summary"] = {"replicates": total, "trustworthy": ok, "invalid": bad}

    if args.json:
        print(json.dumps(report, indent=2))
        return 1 if (bad or report["run_level"]) else 0

    print(f"run: {run_dir}")
    print(f"experiment: {report['experiment']}")
    print(f"replicates: {total}  trustworthy: {ok}  invalid: {bad}")

    for msg in report["run_level"]:
        print(f"\n  RUN-LEVEL: {msg}", file=sys.stderr)
    for rep in report["replicates"]:
        if rep["findings"]:
            print(f"\n  {rep['replicate']}:", file=sys.stderr)
            for f in rep["findings"]:
                print(f"      - {f}", file=sys.stderr)

    if bad or report["run_level"]:
        print(
            f"\nFAIL: this run is not evidence for {bad}/{total} replicate(s). "
            "Fix the instrument and re-run before quoting its numbers.",
            file=sys.stderr,
        )
        return 1

    if args.regrade:
        print("OK: re-grade graded every replicate without a judge-transport gap")
    else:
        print("OK: every replicate loaded the skill, executed, and graded without a transport gap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
