"""Report expected vs performed protected `uip` calls per replicate.

Reads the agent workspace's ``cli_mocks/calls.jsonl`` and the scenario's
source ``data/uip-fixture.json``. Writes ``coverage.json`` and
``coverage.txt`` beside each replicate and prints a run-level table.
"""

from __future__ import annotations

import json
import shlex
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOISE_VALUE_FLAGS = frozenset({"--output"})


def _read_calls(path: Path) -> list[dict]:
    calls: list[dict] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                calls.append(json.loads(line))
    return calls


def _normalized(argv: list[str]) -> tuple[str, ...]:
    expanded: list[str] = []
    for raw in argv:
        if raw.startswith("-") and "=" in raw:
            flag, value = raw.split("=", 1)
            expanded.append(flag)
            if value:
                expanded.append(value)
        else:
            expanded.append(raw)
    cleaned: list[str] = []
    skip_next = False
    for token in expanded:
        if skip_next:
            skip_next = False
            continue
        if token in NOISE_VALUE_FLAGS:
            skip_next = True
            continue
        cleaned.append(token)
    return tuple(sorted(cleaned))


def _task_fixture(task_id: str) -> Path | None:
    marker = f"task_id: {task_id}"
    for task_path in ROOT.glob("**/task.yaml"):
        if marker not in task_path.read_text(encoding="utf-8"):
            continue
        fixture = task_path.parent / "data" / "uip-fixture.json"
        return fixture if fixture.is_file() else None
    return None


def analyze_replicate(rep_dir: Path) -> dict:
    """Build a coverage record for one replicate."""
    task_id = rep_dir.parent.name
    sandbox = rep_dir / "artifacts" / task_id
    calls_path = sandbox / "cli_mocks" / "calls.jsonl"
    fixture_path = _task_fixture(task_id)
    rec: dict = {
        "replicate": rep_dir.name,
        "calls_log_present": calls_path.is_file(),
        "fixture_present": fixture_path is not None,
        "expected": [],
        "calls": [],
        "missing_expected": [],
        "unconfigured": [],
        "response_hits": {},
        "match_rate": None,
    }
    if not calls_path.is_file() or fixture_path is None:
        return rec

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    calls = _read_calls(calls_path)
    expected_status = []
    for spec in fixture.get("expected_calls", []):
        pattern = spec.get("pattern", "")
        minimum = spec.get("min", 1)
        hits = sum(pattern in shlex.join(call.get("argv", [])) for call in calls)
        expected_status.append(
            {
                "pattern": pattern,
                "min": minimum,
                "hits": hits,
                "satisfied": hits >= minimum,
                "description": spec.get("description", ""),
            }
        )

    exact: dict[tuple[str, ...], str] = {}
    normalized: dict[tuple[str, ...], str] = {}
    for response in fixture.get("responses", []):
        argv = response.get("argv", [])
        rendered = shlex.join(argv)
        if response.get("match_mode", "exact") == "normalized":
            normalized[_normalized(argv)] = rendered
        else:
            exact[tuple(argv)] = rendered

    response_counts: Counter[str] = Counter()
    unconfigured: list[str] = []
    for call in calls:
        argv = call.get("argv", [])
        rendered = shlex.join(argv)
        configured = exact.get(tuple(argv)) or normalized.get(_normalized(argv))
        if configured:
            response_counts[configured] += 1
        elif argv[:2] == ["docsai", "ask"]:
            response_counts["docsai ask (passthrough)"] += 1
        else:
            unconfigured.append(rendered)

    rec["expected"] = expected_status
    rec["calls"] = calls
    rec["missing_expected"] = [item for item in expected_status if not item["satisfied"]]
    rec["unconfigured"] = unconfigured
    rec["response_hits"] = dict(response_counts.most_common())
    if expected_status:
        rec["match_rate"] = sum(item["satisfied"] for item in expected_status) / len(expected_status)
    return rec


def write_outputs(rep_dir: Path, rec: dict) -> None:
    (rep_dir / "coverage.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    lines = [
        f"Coverage report for replicate {rec['replicate']}",
        f"  total uip calls: {len(rec['calls'])}",
    ]
    if rec["match_rate"] is not None:
        satisfied = len(rec["expected"]) - len(rec["missing_expected"])
        lines.append(f"  expected hit-rate: {rec['match_rate'] * 100:.0f}% ({satisfied}/{len(rec['expected'])})")
    if rec["missing_expected"]:
        lines.append("  MISSING expected:")
        for item in rec["missing_expected"]:
            lines.append(f"    - {item['pattern']} (got {item['hits']}, need {item['min']})")
    if rec["unconfigured"]:
        lines.append(f"  unconfigured exploration: {len(rec['unconfigured'])}")
        lines.extend(f"    - {value[:100]}" for value in rec["unconfigured"][:10])
    lines.append("  response usage:")
    lines.extend(f"    {count:>3}x {command[:80]}" for command, count in rec["response_hits"].items())
    (rep_dir / "coverage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(run_dir_arg: str) -> int:
    run_dir = Path(run_dir_arg)
    if not run_dir.is_dir():
        print(f"Run dir not found: {run_dir}", file=sys.stderr)
        return 2
    rep_dirs = sorted(path for path in run_dir.iterdir() if path.is_dir() and path.name.isdigit())
    if not rep_dirs:
        print(f"No replicate directories under {run_dir}", file=sys.stderr)
        return 2

    print(f"Coverage report for {run_dir}\n")
    print(f"{'rep':>4}  {'calls':>5}  {'expected':>14}  {'unconfigured':>12}")
    print("-" * 48)
    for rep_dir in rep_dirs:
        rec = analyze_replicate(rep_dir)
        if not rec["calls_log_present"]:
            print(f"{rep_dir.name:>4}  (no call log)")
            continue
        write_outputs(rep_dir, rec)
        satisfied = len(rec["expected"]) - len(rec["missing_expected"])
        total = len(rec["expected"])
        rate = f"{satisfied}/{total} ({(rec['match_rate'] or 0) * 100:.0f}%)"
        print(f"{rep_dir.name:>4}  {len(rec['calls']):>5}  {rate:>14}  {len(rec['unconfigured']):>12}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: coverage_report.py <run_dir>/default/<task_id>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
