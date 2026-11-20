"""The execution tier: run the workflow once per scenario and assert on what it did.

A scenario hands the workflow its input arguments (and any files it reads), then asserts on
what an RPA process can be observed doing: its final state, its output arguments, the lines
it logged and the files it wrote.

    {"name": "cfo-band", "input": {"in_Amount": 60000},
     "expect_outputs": {"out_Route": "CFO"},
     "expect_logs": [{"level": "Info", "mentions": ["CFO"]}]}

Log lines and fault messages are the model's own wording, so they are matched on level and on
the values they must mention (ids, amounts, dates), never on the exact text. `contains` is for
text the task's starting project already writes. `expect_state` defaults to "Closed"
(completed). The runner reports outputs only for a run that completed, so a scenario that
expects a fault asserts on `expect_fault` and on the logs instead. `workflow` runs another file
of the candidate's project in its place, to grade an invoked workflow on its own. `${WORKDIR}`,
`${TODAY}` and `${YESTERDAY}` (yyyy-MM-dd, the grading host's local date, which is the date the
workflow sees) are substituted anywhere in a scenario.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import runner


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    state: str
    messages: list[str] = field(default_factory=list)
    ran: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    passed: bool
    skipped: bool = False
    scenarios: list[ScenarioResult] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def _substitute(value, tokens: dict[str, str]):
    if isinstance(value, str):
        for token, text in tokens.items():
            value = value.replace(token, text)
        return value
    if isinstance(value, list):
        return [_substitute(v, tokens) for v in value]
    if isinstance(value, dict):
        return {_substitute(k, tokens): _substitute(v, tokens) for k, v in value.items()}
    return value


def _number(value) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def diff(expected, actual, path: str = "") -> str | None:
    """First difference between an expected and an actual value, or None. Numbers compare by value."""
    want, got = _number(expected), _number(actual)
    if want is not None or got is not None:
        return None if want == got else f"{path or 'value'}: expected {expected!r}, got {actual!r}"
    if isinstance(expected, dict) and "columns" in expected and "rows" in expected:
        return _diff_table(expected, actual, path)
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return f"{path}: expected a list, got {actual!r}"
        if len(expected) != len(actual):
            return f"{path}: expected {len(expected)} items, got {len(actual)}: {actual!r}"
        for i, (e, a) in enumerate(zip(expected, actual, strict=True)):
            if (d := diff(e, a, f"{path}[{i}]")) is not None:
                return d
        return None
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return f"{path}: expected an object, got {actual!r}"
        for key, e in expected.items():
            if key not in actual:
                return f"{path}.{key}: missing"
            if (d := diff(e, actual[key], f"{path}.{key}")) is not None:
                return d
        return None
    return None if expected == actual else f"{path or 'value'}: expected {expected!r}, got {actual!r}"


def _diff_table(expected: dict, actual, path: str) -> str | None:
    if not isinstance(actual, dict) or "columns" not in actual:
        return f"{path}: expected a DataTable, got {actual!r}"
    want_cols = [c if isinstance(c, str) else c["name"] for c in expected["columns"]]
    got_cols = [c["name"] for c in actual["columns"]]
    if want_cols != got_cols:
        return f"{path}: columns are {got_cols}, expected {want_cols}"
    for want, got in zip(expected["columns"], actual["columns"], strict=True):
        if isinstance(want, dict) and "type" in want and want["type"] != got["type"]:
            return f"{path}: column {got['name']} is {got['type']}, expected {want['type']}"
    rows = actual["rows"]
    if len(rows) != len(expected["rows"]):
        return f"{path}: {len(rows)} rows, expected {len(expected['rows'])}: {rows!r}"
    for i, (want, got) in enumerate(zip(expected["rows"], rows, strict=True)):
        if (d := diff(want, got, f"{path} row {i}")) is not None:
            return d
    return None


def _mentions(text: str, values: list[str]) -> bool:
    # Whole values, ignoring case: `CL-1` must not be found inside `CL-10`.
    return all(re.search(rf"(?<![\w-]){re.escape(str(v))}(?![\w-])", text, re.IGNORECASE) for v in values)


def _log_matches(want: dict, entry: dict) -> bool:
    message = entry.get("message") or ""
    if "level" in want and want["level"] != entry.get("level"):
        return False
    if "contains" in want and want["contains"] not in message:
        return False
    return _mentions(message, want.get("mentions") or [])


def _check_logs(scenario: dict, logs: list[dict]) -> list[str]:
    messages = []
    # Ordered, not contiguous: extra lines between the expected ones are allowed.
    cursor = 0
    for want in scenario.get("expect_logs") or []:
        while cursor < len(logs) and not _log_matches(want, logs[cursor]):
            cursor += 1
        if cursor == len(logs):
            messages.append(f"expected a log line {want} (in order); logged: {[e['message'] for e in logs]}")
            break
        cursor += 1
    for want in scenario.get("expect_log_counts") or []:
        seen = sum(1 for e in logs if _log_matches(want, e))
        if seen != want["count"]:
            messages.append(f"{seen} log lines match {want}, expected {want['count']}")
    for want in scenario.get("expect_not_logged") or []:
        if any(_log_matches(want, e) for e in logs):
            messages.append(f"a log line matches {want}, and none should")
    return messages


def _check(scenario: dict, result: dict, workdir: Path) -> list[str]:
    messages = []
    state = result.get("state")
    want_state = scenario.get("expect_state", "Closed")
    fault = result.get("fault") or {}
    if state != want_state:
        detail = f": {fault.get('type')}: {fault.get('message')}" if fault else ""
        errors = "; ".join(e.get("message", "") for e in result.get("errors") or [])
        messages.append(f"final state {state}, expected {want_state}{detail}{(' ' + errors) if errors else ''}")
        return messages

    if (want_fault := scenario.get("expect_fault")) is not None:
        if want_fault.get("type") and fault.get("type") != want_fault["type"]:
            messages.append(f"fault is {fault.get('type')}, expected {want_fault['type']}")
        if not _mentions(fault.get("message") or "", want_fault.get("mentions") or []):
            messages.append(f"fault message {fault.get('message')!r} does not mention {want_fault['mentions']}")

    outputs = result.get("outputs") or {}
    for name, want in (scenario.get("expect_outputs") or {}).items():
        if name not in outputs:
            messages.append(f"output {name} was not returned")
        elif (d := diff(want, outputs[name], name)) is not None:
            messages.append(d)

    messages += _check_logs(scenario, result.get("logs") or [])

    for rel, want in (scenario.get("expect_files") or {}).items():
        target = workdir / rel
        if not target.exists():
            messages.append(f"{rel} was not written")
            continue
        # utf-8-sig: Append Line writes a BOM when it creates the file.
        got = target.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        if isinstance(want, dict) and "lines" in want:
            # Append Line writes its newline before the text, so a correct log can hold blank lines.
            lines = [line.rstrip() for line in got.split("\n") if line.strip()]
            if lines != want["lines"]:
                messages.append(f"{rel} lines are {lines!r}, expected {want['lines']!r}")
        elif isinstance(want, dict):
            messages += [f"{rel} does not contain {s!r}" for s in want.get("contains", []) if s not in got]
        elif got.rstrip("\n") != want.replace("\r\n", "\n").rstrip("\n"):
            messages.append(f"{rel} content differs: expected {want!r}, got {got!r}")
    for rel in scenario.get("expect_no_files") or []:
        if (workdir / rel).exists():
            messages.append(f"{rel} was written and must not be")
    return messages


def run_scenario(candidate: Path, scenario: dict) -> ScenarioResult:
    name = scenario["name"]
    if rel := scenario.get("workflow"):
        candidate = candidate.parent / rel
        if not candidate.exists():
            return ScenarioResult(name, False, "Missing", [f"{rel} was not created"])
    with tempfile.TemporaryDirectory(prefix="xaml-scenario-") as tmp:
        workdir = Path(tmp).resolve()
        today = date.today()
        tokens = {
            "${WORKDIR}": str(workdir),
            "${TODAY}": today.isoformat(),
            "${YESTERDAY}": (today - timedelta(days=1)).isoformat(),
        }
        scenario = _substitute(scenario, tokens)
        for rel, content in (scenario.get("files") or {}).items():
            target = workdir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        try:
            result = runner.run(
                candidate, scenario.get("input") or {}, workdir, timeout=float(scenario.get("timeout", 30))
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            return ScenarioResult(name, False, "RunnerError", [f"runner failed: {exc}"])
        messages = _check(scenario, result, workdir)
    return ScenarioResult(
        name,
        not messages,
        result.get("state", "?"),
        messages,
        ran=[r["displayName"] for r in result.get("trace") or []],
        logs=[f"[{e['level']}] {e['message']}" for e in result.get("logs") or []],
    )


def t_execution(candidate: Path, spec: dict) -> ExecutionResult:
    scenarios = spec.get("scenarios") or []
    if not scenarios:
        return ExecutionResult(True, skipped=True, messages=["spec declares no scenarios"])
    try:
        runner.locate()
    except runner.RunnerMissingError as exc:
        # Not a skip: a grade that silently stopped checking behaviour is worse than none.
        return ExecutionResult(False, messages=[f"runner unavailable: {exc}"])
    results = [run_scenario(candidate, s) for s in scenarios]
    return ExecutionResult(all(r.passed for r in results), scenarios=results)
