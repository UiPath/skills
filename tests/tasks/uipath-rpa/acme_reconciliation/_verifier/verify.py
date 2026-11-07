"""Entry point: grade one candidate `.xaml` workflow against a task spec.

    python3 _verifier/verify.py --spec specs/invoice_routing.json --candidate Main.xaml

Prints a human-readable report, writes a machine-readable one to `--reward-file`, and exits 0
only when the score clears the task's threshold, so it drops straight into a coder-eval
`run_command` criterion.

`--tiers static` runs parse, untouched, compile and contract, which read the workflow;
`--tiers runtime` runs parse and execution, which runs it. Every gate is hard, every tier runs
even after one fails, and the report carries `behavioural_score` next to `score`: the fraction
of scenarios that behaved, so a near miss is distinguishable from the wrong process.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script, not imported
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "_verifier"

from _verifier import execute, tiers


def grade(spec: dict, candidate: Path, only: str = "all", spec_dir: Path | None = None) -> dict:
    report: dict = {"candidate": str(candidate), "tiers": [], "score": 0.0, "tiers_run": only}
    static, runtime = only in ("all", "static"), only in ("all", "runtime")

    parsed = tiers.t_parse(candidate)
    report["tiers"].append({"name": parsed.name, "status": parsed.status, "messages": parsed.messages})
    if not parsed.passed:
        report["reason"] = f"unparseable: {'; '.join(parsed.messages)}"
        return report

    blocking: list[str] = []
    if static:
        compiled, inspection = tiers.t_compile(candidate)
        gates = [
            tiers.t_untouched(candidate, spec, spec_dir),
            compiled,
            tiers.t_contract(inspection, spec, candidate),
        ]
        for result in gates:
            report["tiers"].append({"name": result.name, "status": result.status, "messages": result.messages})
        blocking += [g.name for g in gates if not g.passed and not g.skipped]

    if runtime:
        run = execute.t_execution(candidate, spec)
        report["execution"] = {
            "skipped": run.skipped,
            "scenarios": [
                {
                    "name": s.name,
                    "passed": s.passed,
                    "state": s.state,
                    "ran": s.ran,
                    "logs": s.logs,
                    "messages": s.messages,
                }
                for s in run.scenarios
            ],
        }
        report["tiers"].append(
            {
                "name": "execution",
                "status": "skip" if run.skipped else ("pass" if run.passed else "FAIL"),
                "messages": run.messages
                + [f"{s.name}: {'; '.join(s.messages)}" for s in run.scenarios if not s.passed],
            }
        )
        if not run.passed and not run.skipped:
            blocking.append("execution")
        report["behavioural_score"] = (
            round(sum(1 for s in run.scenarios if s.passed) / len(run.scenarios), 4) if run.scenarios else 0.0
        )

    if blocking:
        report["reason"] = f"gate failed: {', '.join(blocking)}"
    else:
        report["score"] = 1.0
    return report


def render(report: dict) -> str:
    lines = [f"candidate: {report['candidate']}"]
    for tier in report["tiers"]:
        lines.append(f"  [{tier['status']:>4}] {tier['name']}")
        lines += [f"           {msg}" for msg in tier["messages"]]
    for scenario in (report.get("execution") or {}).get("scenarios", []):
        mark = "pass" if scenario["passed"] else "FAIL"
        lines.append(f"  [{mark:>4}] scenario {scenario['name']} -> {scenario['state']}")
        if not scenario["passed"]:
            lines.append(f"           logs: {scenario['logs'] or '(none)'}")
        lines += [f"           {msg}" for msg in scenario["messages"]]
    if report.get("reason"):
        lines.append(f"  reason: {report['reason']}")
    behavioural = report.get("behavioural_score")
    if behavioural is not None and behavioural != report["score"]:
        lines.append(f"  behaviour alone would have scored {behavioural:.4f}")
    lines.append(f"score: {report['score']:.4f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Grade a UiPath XAML workflow against a task spec.")
    ap.add_argument("--spec", required=True, help="path to the task's spec json")
    ap.add_argument("--candidate", help="path to the .xaml under test (default: spec's `candidate`)")
    ap.add_argument("--cwd", default=".", help="directory the candidate is resolved against")
    ap.add_argument("--reward-file", default="reward.json")
    ap.add_argument("--tiers", default="all", choices=("all", "static", "runtime"))
    args = ap.parse_args(argv)

    spec_path = Path(args.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    # Tasks name the file they asked for. Falling back to "any .xaml in the directory" would
    # let a model score by leaving a stray file behind.
    candidate = Path(args.candidate) if args.candidate else Path(args.cwd) / spec.get("candidate", "Main.xaml")
    if not candidate.exists():
        report = {
            "candidate": str(candidate),
            "tiers": [{"name": "parse", "status": "FAIL", "messages": [f"{candidate} was not created"]}],
            "score": 0.0,
            "tiers_run": args.tiers,
            "reason": "candidate file missing",
        }
    else:
        report = grade(spec, candidate.resolve(), args.tiers, spec_path.parent)

    print(render(report))
    threshold = float(spec.get("pass_threshold", 1.0))
    report["passed"] = report["score"] >= threshold
    report["threshold"] = threshold
    Path(args.reward_file).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
