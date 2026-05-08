"""Coverage reporter: expected vs performed uip commands per replicate.

Reads:
  - <run_dir>/<NN>/artifacts/<task_id>/mocks/.calls.jsonl
      one JSON record per uip invocation written by the mock dispatcher
  - <run_dir>/<NN>/artifacts/<task_id>/mocks/responses/manifest.json
      the manifest's `expected_calls` declares minimum-coverage patterns

Writes per replicate:
  - <run_dir>/<NN>/coverage.json         structured comparison
  - <run_dir>/<NN>/coverage.txt          human-readable summary

Also prints a run-level table to stdout.

Usage:
    python tmp/coverage_report.py runs/<run-timestamp>/default/<task_id>
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def analyze_replicate(rep_dir: Path) -> dict:
    """Build a coverage record for one replicate."""
    sandbox = rep_dir / "artifacts" / rep_dir.parent.name
    calls_path = sandbox / "mocks" / ".calls.jsonl"
    manifest_path = sandbox / "mocks" / "responses" / "manifest.json"

    rec: dict = {
        "replicate": rep_dir.name,
        "calls_log_present": calls_path.is_file(),
        "manifest_present": manifest_path.is_file(),
        "expected": [],
        "calls": [],
        "missing_expected": [],
        "unmocked": [],
        "rule_hits": {},
        "match_rate": None,
    }
    if not calls_path.is_file() or not manifest_path.is_file():
        return rec

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("expected_calls", [])
    calls: list[dict] = []
    with calls_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                calls.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Per-pattern hit counts
    expected_status = []
    for spec in expected:
        pat = spec.get("pattern", "")
        minimum = spec.get("min", 1)
        hits = sum(1 for c in calls if pat in c.get("args", ""))
        expected_status.append({
            "pattern": pat,
            "min": minimum,
            "hits": hits,
            "satisfied": hits >= minimum,
            "description": spec.get("description", ""),
        })

    # Rule usage
    rule_counts: Counter = Counter()
    for c in calls:
        rule = c.get("matched_rule")
        if rule:
            rule_counts[rule] += 1

    # Unmocked calls
    unmocked = [c.get("args", "") for c in calls if c.get("matched_rule") is None]

    rec["expected"] = expected_status
    rec["calls"] = calls
    rec["missing_expected"] = [e for e in expected_status if not e["satisfied"]]
    rec["unmocked"] = unmocked
    rec["rule_hits"] = dict(rule_counts.most_common())
    if expected_status:
        rec["match_rate"] = sum(1 for e in expected_status if e["satisfied"]) / len(expected_status)

    return rec


def write_outputs(rep_dir: Path, rec: dict) -> None:
    (rep_dir / "coverage.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    lines = []
    lines.append(f"Coverage report for replicate {rec['replicate']}")
    lines.append(f"  total uip calls : {len(rec['calls'])}")
    if rec["match_rate"] is not None:
        lines.append(f"  expected hit-rate: {rec['match_rate']*100:.0f}% "
                     f"({len(rec['expected']) - len(rec['missing_expected'])}/{len(rec['expected'])})")
    if rec["missing_expected"]:
        lines.append("  MISSING expected:")
        for e in rec["missing_expected"]:
            lines.append(f"    - {e['pattern']} (got {e['hits']}, need {e['min']})")
    if rec["unmocked"]:
        lines.append(f"  unmocked (exploration): {len(rec['unmocked'])}")
        for u in rec["unmocked"][:10]:
            lines.append(f"    - {u[:100]}")
    lines.append("  rule usage:")
    for rule, n in rec["rule_hits"].items():
        lines.append(f"    {n:>3}x {rule[:80]}")
    (rep_dir / "coverage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(run_dir_arg: str) -> int:
    run_dir = Path(run_dir_arg)
    if not run_dir.is_dir():
        print(f"Run dir not found: {run_dir}", file=sys.stderr)
        return 2

    rep_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    if not rep_dirs:
        print(f"No replicate directories under {run_dir}", file=sys.stderr)
        return 2

    print(f"Coverage report for {run_dir}\n")
    print(f"{'rep':>4}  {'calls':>5}  {'expected':>14}  {'unmocked':>8}  {'top exploration':<60}")
    print("-" * 100)
    for rep_dir in rep_dirs:
        rec = analyze_replicate(rep_dir)
        if not rec["calls_log_present"]:
            print(f"{rep_dir.name:>4}  (no .calls.jsonl)")
            continue
        write_outputs(rep_dir, rec)
        nm = len(rec["expected"]) - len(rec["missing_expected"])
        tot = len(rec["expected"])
        rate = f"{nm}/{tot} ({(rec['match_rate'] or 0)*100:.0f}%)"
        top_unmocked = rec["unmocked"][0] if rec["unmocked"] else ""
        print(f"{rep_dir.name:>4}  {len(rec['calls']):>5}  {rate:>14}  {len(rec['unmocked']):>8}  {top_unmocked[:60]}")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tmp/coverage_report.py <run_dir>/default/<task_id>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
