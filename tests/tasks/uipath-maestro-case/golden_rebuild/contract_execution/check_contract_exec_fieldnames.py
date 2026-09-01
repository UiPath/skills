#!/usr/bin/env python3
"""ContractExecution rebuild: schema field-name casing and null-guard grader.

This case surfaced a build-then-fail-at-runtime class of bug worth its own
criterion. Task-output objects (a connector event payload, an api-workflow
`response`, an agent `analysisResult`) are dereferenced by sub-property name,
and those names are case-sensitive at runtime but invisible to
``uip maestro case validate``. A build that renames `request_body` to
`RequestBody` validates clean, publishes clean, and then dies in Studio Web
with "RequestBody not found, did you mean request_body" - taking every gate
that reads it with it.

The same expressions must also null-guard the dereference:
``vars.X?.prop`` (or the older ``(vars.X || {}).prop``). An unguarded ``vars.X.prop`` throws
"Cannot read property 'prop' of null" the first time the producing task has
not run.

This grader therefore asserts, against the field names declared in the task's
own ``fixtures/sdd.md``:

  - every dotted access off a task-output object in the caseplan uses a
    property name the SDD declares, with the SDD's exact casing
  - no dotted access off a ``vars.`` reference is unguarded
  - every extract output's ``=<root>.<field>`` source path uses an SDD field
    name, with the SDD's exact casing
  - the webhook response output's JSON-schema property keys are exactly the
    SDD's declared event output fields (this is where a PascalCasing
    ``--output json`` serializer leaks its key casing into the artifact)
  - every SDD-declared dotted access is actually present, so the checker
    cannot pass by the build simply dropping the expressions
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import find_stages, iter_tasks, read_caseplan  # noqa: E402

EXPECTED_CASEPLAN = os.path.join("ContractExecution", "ContractExecution", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

# Null-safe forms, both accepted: `vars.X?.prop` (preferred - also guards method
# calls and chains flat) and `(vars.X || {}).prop` (older, still valid).
GUARDED_PATTERNS = (
    re.compile(r"vars\.([A-Za-z_]\w*)\s*\?\.\s*([A-Za-z_]\w*)"),
    re.compile(r"\(\s*vars\.([A-Za-z_]\w*)\s*\|\|\s*\{\s*\}\s*\)\s*\.\s*([A-Za-z_]\w*)"),
)


def _guarded_derefs(expression: str):
    """Yield (variable, property) for every null-safe dereference, either form."""
    for pattern in GUARDED_PATTERNS:
        yield from pattern.findall(expression)
# `vars.X.prop` - unguarded; the leading lookbehind keeps it from matching
# inside the guarded form above.
UNGUARDED_RE = re.compile(r"(?<![.\w])vars\.([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)")
# An extract output's schema path, e.g. `=response.riskFlags`.
SOURCE_PATH_RE = re.compile(r"^\s*=\s*([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)\s*$")
# Roots that are language/runtime objects, not task-output schemas.
EXEMPT_ROOTS = frozenset({"vars", "metadata", "JSON", "Math", "String", "Object", "Number"})

XREF_PROP_RE = re.compile(r"\$xref\([^)]*\)\s*\.\s*([A-Za-z_]\w*)")
EXTRACT_ROW_RE = re.compile(r"^\|\s*([A-Za-z_]\w*)\.([A-Za-z_]\w*)\s*\|\s*->", re.M)
EVENT_ROW_RE = re.compile(r"^\|[^|\n]*\|[^|\n]*\|\s*EVENT\s*\|[^|\n]*\|([^|\n]*)\|", re.M)
FIELD_DECL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*:\s*string\b")


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _read_plan() -> dict:
    if len(sys.argv) > 1:
        return read_caseplan(sys.argv[1])
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def parse_fixture() -> dict:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            sdd = stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")

    dotted = set(XREF_PROP_RE.findall(sdd))
    if len(dotted) < 4:
        _fail(
            "fixture parse error: expected >=4 distinct $xref dotted-access property "
            f"names; got {sorted(dotted)}"
        )
    extract_paths = {f"{root}.{field}" for root, field in EXTRACT_ROW_RE.findall(sdd)}
    if len(extract_paths) < 2:
        _fail(
            "fixture parse error: expected >=2 `<root>.<field> | ->` extract rows; got "
            f"{sorted(extract_paths)}"
        )
    event_fields: set[str] = set()
    for cell in EVENT_ROW_RE.findall(sdd):
        event_fields.update(FIELD_DECL_RE.findall(cell))
    if len(event_fields) != 2:
        _fail(
            "fixture parse error: expected 2 webhook event output fields in the Section 4 "
            f"operations table; got {sorted(event_fields)}"
        )
    return {
        "dotted": dotted,
        "extract_paths": extract_paths,
        "extract_fields": {path.split(".", 1)[1] for path in extract_paths},
        "event_fields": event_fields,
    }


def _expressions(plan: dict):
    """Yield (where, expression) for every author-controlled expression string."""
    for stage in find_stages(plan, include_exception=True):
        label = (stage.get("data") or {}).get("label") or stage.get("id")
        for kind in ("entryConditions", "exitConditions"):
            for condition in ((stage.get("data") or {}).get(kind) or []):
                for group in condition.get("rules") or []:
                    for rule in group or []:
                        expression = (rule or {}).get("conditionExpression")
                        if isinstance(expression, str):
                            yield f"stage {label!r} {kind} [{condition.get('displayName')}]", expression
        for rule in (stage.get("data") or {}).get("slaRules") or []:
            expression = rule.get("expression")
            if isinstance(expression, str):
                yield f"stage {label!r} SLA [{rule.get('displayName')}]", expression

    for task in iter_tasks(plan):
        name = task.get("displayName") or task.get("id")
        for kind in ("entryConditions", "exitConditions"):
            for condition in task.get(kind) or []:
                for group in condition.get("rules") or []:
                    for rule in group or []:
                        expression = (rule or {}).get("conditionExpression")
                        if isinstance(expression, str):
                            yield f"task {name!r} {kind}", expression
        data = task.get("data") or {}
        for item in data.get("inputs") or []:
            value = item.get("value")
            if isinstance(value, str):
                yield f"task {name!r} input {item.get('name')!r}", value

    for condition in ((plan.get("metadata") or {}).get("caseExitRules") or []):
        for group in condition.get("rules") or []:
            for rule in group or []:
                expression = (rule or {}).get("conditionExpression")
                if isinstance(expression, str):
                    yield f"case exit [{condition.get('displayName')}]", expression
    for rule in ((plan.get("metadata") or {}).get("slaRules") or []):
        expression = rule.get("expression")
        if isinstance(expression, str):
            yield f"case SLA [{rule.get('displayName')}]", expression


def _output_sources(plan: dict):
    for task in iter_tasks(plan):
        name = task.get("displayName") or task.get("id")
        for output in ((task.get("data") or {}).get("outputs") or []):
            source = output.get("source")
            if isinstance(source, str):
                yield f"task {name!r} output {output.get('name')!r}", source


def _casing_hint(actual: str, allowed: set[str]) -> str:
    match = next((name for name in allowed if _norm(name) == _norm(actual)), None)
    if match is None:
        return f"not declared by the SDD (declared: {sorted(allowed)})"
    return (
        f"the SDD declares {match!r} - property names are case-sensitive at runtime and "
        "invisible to `validate`"
    )


def _check_expressions(plan: dict, fixture: dict):
    allowed = fixture["dotted"]
    seen: set[str] = set()
    for where, expression in _expressions(plan):
        for variable, prop in UNGUARDED_RE.findall(expression):
            _fail(
                f"{where}: unguarded dotted access `vars.{variable}.{prop}` in "
                f"{expression!r} - optional-chain it: `vars.{variable}?.{prop}` "
                "(or the older `(vars.X || {}).Y`), otherwise the expression throws "
                "before the producing task has run"
            )
        for variable, prop in _guarded_derefs(expression):
            if prop not in allowed:
                _fail(
                    f"{where}: `vars.{variable}?.{prop}` uses property {prop!r}, "
                    f"{_casing_hint(prop, allowed)}"
                )
            seen.add(prop)
    missing = sorted(allowed - seen)
    if missing:
        _fail(
            "the SDD dereferences these task-output properties but the caseplan never "
            f"does: {missing}"
        )


def _check_output_sources(plan: dict, fixture: dict):
    allowed_paths = fixture["extract_paths"]
    allowed_fields = fixture["extract_fields"]
    seen: set[str] = set()
    for where, source in _output_sources(plan):
        match = SOURCE_PATH_RE.fullmatch(source)
        if match is None:
            continue
        root, field = match.groups()
        if root in EXEMPT_ROOTS:
            continue
        path = f"{root}.{field}"
        if path not in allowed_paths:
            _fail(
                f"{where}: extract source `={path}` is not an SDD extract path; "
                f"{_casing_hint(field, allowed_fields)}"
            )
        seen.add(path)
    missing = sorted(allowed_paths - seen)
    if missing:
        _fail(f"the SDD declares these extract source paths but the caseplan has none: {missing}")


def _check_event_schema(plan: dict, fixture: dict):
    matches = [task for task in iter_tasks(plan) if task.get("type") == "wait-for-connector"]
    if len(matches) != 1:
        _fail(f"expected exactly 1 wait-for-connector task; got {len(matches)}")
    outputs = [
        output
        for output in ((matches[0].get("data") or {}).get("outputs") or [])
        if output.get("custom") is not True and isinstance(output.get("body"), dict)
    ]
    if len(outputs) != 1:
        _fail(
            "the wait-for-connector task must expose exactly one event output carrying a "
            f"JSON schema `body`; got {len(outputs)}"
        )
    properties = (outputs[0]["body"].get("properties") or {})
    if not isinstance(properties, dict) or not properties:
        _fail("the webhook event output schema declares no properties")
    actual = set(properties)
    if actual != fixture["event_fields"]:
        _fail(
            "webhook event output schema property keys differ from the SDD's declared "
            "event output fields - a PascalCasing `--output json` serializer leaks its "
            "own key casing here\n"
            f"  actual={sorted(actual)}\n"
            f"  expected={sorted(fixture['event_fields'])}"
        )


def main():
    plan = _read_plan()
    fixture = parse_fixture()
    _check_expressions(plan, fixture)
    _check_output_sources(plan, fixture)
    _check_event_schema(plan, fixture)
    print(
        "OK: every task-output dereference is null-guarded and uses the SDD's exact "
        f"property casing ({sorted(fixture['dotted'])}), every extract source path "
        f"matches the SDD ({sorted(fixture['extract_paths'])}), and the webhook event "
        f"schema keys are {sorted(fixture['event_fields'])}"
    )


if __name__ == "__main__":
    main()
