#!/usr/bin/env python3
"""Score eval rows the way Studio Web's Evaluations panel does — `uipath-exact-match`
as a strict deep-equal of the workflow's RAW output against `expectedOutput`, under
the evaluator's `targetOutputKey`.

The raw output is read from the executor's debug log, not from the CLI's `Data`
envelope: `uip` PascalCases every key in `Data` (`grade` -> `Grade`), which would hide
exactly the key-casing mismatches the panel fails on.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RESPONSE_LINE = re.compile(r'Response task evaluated successfully for "[^"]*": (\{.*\})\s*$')


def run_row(workflow_path, inputs, timeout=120):
    """Return (ok, raw_output, error). `ok` is False when the run itself failed."""
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as handle:
        log_path = handle.name
    cmd = [
        "uip", "api-workflow", "run", str(workflow_path),
        "--input-arguments", json.dumps(inputs),
        "--no-auth", "--output", "json", "--log-level", "debug", "--log-file", log_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, None, "run timed out"
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, None, f"non-JSON CLI output (exit {proc.returncode}): {proc.stdout[:300]}"
    if envelope.get("Result") != "Success":
        return False, None, f"run failed: {json.dumps(envelope)[:300]}"
    raw = None
    for line in Path(log_path).read_text(errors="replace").splitlines():
        match = RESPONSE_LINE.search(line)
        if match:
            raw = json.loads(match.group(1)).get("response")
    if raw is None:
        return False, None, "no Response evaluation found in debug log"
    return True, raw, None


def deep_equal(actual, expected):
    """lodash `isEqual` semantics for JSON data: booleans are not numbers, key order is
    irrelevant, every key / type / shape must match."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(deep_equal(actual[k], expected[k]) for k in actual)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(deep_equal(a, e) for a, e in zip(actual, expected))
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return actual == expected
    return type(actual) is type(expected) and actual == expected


_MISSING = object()


def value_at_path(value, path):
    for segment in [s for s in path.split(".") if s]:
        if not isinstance(value, dict) or segment not in value:
            return _MISSING
        value = value[segment]
    return value


def exact_match(actual, expected, target_key):
    """Mirror the panel's scorer: '*' / empty compares whole objects; a dotted path digs
    into BOTH sides; a list requires every path to match; missing on both sides fails."""
    if isinstance(target_key, list):
        return bool(target_key) and all(exact_match(actual, expected, key) for key in target_key)
    if isinstance(target_key, str) and target_key not in ("", "*"):
        a, e = value_at_path(actual, target_key), value_at_path(expected, target_key)
        if a is _MISSING or e is _MISSING:
            return False
        return deep_equal(a, e)
    return deep_equal(actual, expected)


def wrap_output(raw):
    return raw if isinstance(raw, dict) else {"result": raw}


def parse_expected(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"result": value}
    return value


def load_eval_sets(project_dir):
    return sorted(Path(project_dir).glob("evals/*/eval-sets/*.json"))


def load_evaluators(project_dir):
    """{file base name: evaluator}, keyed the way `evaluatorRefs` / `evaluationCriterias` are."""
    return {p.stem: json.loads(p.read_text()) for p in sorted(Path(project_dir).glob("evals/*/evaluators/*.json"))}


def score_project(project_dir, workflow_path=None):
    """Run every row of every eval set through the workflow and score it with its
    referenced evaluators. Returns a list of dicts; `verdict` is pass|fail|error."""
    project_dir = Path(project_dir)
    workflow_path = Path(workflow_path or project_dir / "Workflow.json")
    evaluators = load_evaluators(project_dir)
    results = []
    for set_path in load_eval_sets(project_dir):
        eval_set = json.loads(set_path.read_text())
        refs = [str(r).removesuffix(".json") for r in eval_set.get("evaluatorRefs", [])]
        for row in eval_set.get("evaluations", []):
            criterias = row.get("evaluationCriterias") or {}
            ok, raw, error = run_row(workflow_path, row.get("inputs") or {})
            actual = wrap_output(raw) if ok else None
            for ref in refs:
                evaluator = evaluators.get(ref)
                criteria = criterias.get(ref) or criterias.get(f"{ref}.json")
                record = {"set": set_path.name, "row": row.get("name") or row.get("id"), "evaluator": ref,
                          "inputs": row.get("inputs"), "actual": actual, "expected": None}
                if evaluator is None or evaluator.get("evaluatorTypeId") != "uipath-exact-match":
                    record.update(verdict="error", error=f"evaluator {ref!r} missing or not uipath-exact-match")
                elif criteria is None or "expectedOutput" not in criteria:
                    record.update(verdict="error", error=f"row has no expectedOutput for {ref!r}")
                elif not ok:
                    record.update(verdict="error", error=error)
                else:
                    expected = parse_expected(criteria["expectedOutput"])
                    target = (evaluator.get("evaluatorConfig") or {}).get("targetOutputKey", "*")
                    record.update(expected=expected,
                                  verdict="pass" if exact_match(actual, expected, target) else "fail")
                results.append(record)
    return results


def print_results(results):
    for r in results:
        detail = r.get("error") or f"actual={json.dumps(r['actual'])} expected={json.dumps(r['expected'])}"
        print(f"[{r['verdict'].upper():5}] {r['set']} :: {r['row']} ({r['evaluator']}) inputs={json.dumps(r['inputs'])} {detail}")


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    rows = score_project(project)
    print_results(rows)
    sys.exit(0 if rows and all(r["verdict"] == "pass" for r in rows) else 1)
