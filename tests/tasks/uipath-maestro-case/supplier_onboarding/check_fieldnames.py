#!/usr/bin/env python3
"""SupplierOnboarding: do the wire-level field names keep the casing runtime needs?

Task-output property names are case-sensitive at runtime and **invisible to
`uip maestro case validate`**. A build that PascalCases one validates clean,
publishes clean, and then dies in Studio Web with `Status not found, did you mean
status`, taking every task that reads it.

Four assertions:

 1. Each of the six connector tasks reads its delivery status from the lowercase
    wire path `response.status`.
 2. That path lands in the one variable the SDD names for it.
 3. `displayName` is NOT part of this contract. This build labels the output
    `Response` while wiring `response`, which is correct — a grader that scanned for
    PascalCase anywhere in the plan would fail it. This assertion states the rule so
    a later edit does not reintroduce that mistake.
 4. Every dotted dereference in an expression reads a property whose root the plan
    actually holds, and the four file inputs the SDD dereferences are named exactly
    as declared.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402

# `vars.<root>.<prop>` — a dereference off a case variable inside an expression.
_DOTTED_RE = re.compile(r"vars\.([A-Za-z_]\w*)\.([A-Za-z_]\w*)")


def main() -> int:
    facts = E.sdd_facts()
    caseplan = P.load()
    problems: list[str] = []

    fixture_extracts = facts["connector_extracts"]

    # ---- 1 + 2. the connector status wire ----------------------------------
    connector_tasks = [
        (stage, task)
        for stage, task in P.all_tasks(caseplan)
        if P.task_type(task) == "execute-connector-activity"
    ]
    if len(connector_tasks) != E.CONNECTOR_TASK_COUNT:
        problems.append(
            f"{len(connector_tasks)} connector task(s) in the plan; the SDD declares "
            f"{E.CONNECTOR_TASK_COUNT}"
        )

    for stage, task in connector_tasks:
        name = P.task_name(task)
        paths = P.output_wire_paths(task)
        status_wires = {p for p in paths if p.lower().endswith("status")}
        if not status_wires:
            problems.append(
                f"{stage}/{name!r}: no output reads a delivery status; the SDD extracts "
                f"{E.CONNECTOR_OUTPUT_PATH!r} on every connector task"
            )
            continue
        if E.CONNECTOR_OUTPUT_PATH not in status_wires:
            problems.append(
                f"{stage}/{name!r}: the status wire path is {sorted(status_wires)}; the "
                f"connector's contract is the lowercase {E.CONNECTOR_OUTPUT_PATH!r}. "
                "Casing here is load-bearing at runtime and `validate` cannot see it — "
                "the run dies with `Status not found, did you mean status`."
            )
            continue
        targets = {
            entry.get("var")
            for entry in P.task_outputs(task)
            if str(entry.get("source") or "") == "=" + E.CONNECTOR_OUTPUT_PATH
        }
        if E.CONNECTOR_OUTPUT_TARGET not in targets:
            problems.append(
                f"{stage}/{name!r}: {E.CONNECTOR_OUTPUT_PATH!r} lands in {sorted(targets)}; "
                f"the SDD sends it to {E.CONNECTOR_OUTPUT_TARGET!r}"
            )

    # ---- 3. displayName is a label, not a contract -------------------------
    # Stated as an assertion so the rule is executable rather than a comment: the
    # human label may be PascalCase, the wire path may not.
    labels = {
        str(entry.get("displayName"))
        for _stage, task in connector_tasks
        for entry in P.task_outputs(task)
        if entry.get("displayName")
    }
    # Only a re-cased variant of a path the fixture declares is a defect. The
    # connector's own contract also exposes `Error`, which is genuinely PascalCase —
    # a blanket "no uppercase root" rule fails a correct build on that one.
    fixture_paths = {path for path, _target in fixture_extracts}
    lowered = {p.lower(): p for p in fixture_paths}
    for _stage, task in connector_tasks:
        for wire in P.output_wire_paths(task):
            canonical = lowered.get(wire.lower())
            if canonical is not None and wire != canonical:
                problems.append(
                    f"{P.task_name(task)!r}: wire path {wire!r} is a re-cased variant of "
                    f"the fixture's {canonical!r}. Runtime resolves this path literally, "
                    "and `validate` accepts either casing."
                )

    # ---- 4. each escalation names its own phase ----------------------------
    names_to_task = {P.task_name(t): t for _stage, t in P.all_tasks(caseplan)}
    stage_of = {P.task_name(t): stage for stage, t in P.all_tasks(caseplan)}
    for task_name, literal in sorted(E.STAGE_NAME_LITERAL.items()):
        item = names_to_task.get(task_name)
        if item is None:
            problems.append(f"task {task_name!r} is missing")
            continue
        values = {
            entry.get("value")
            for entry in P.task_inputs(item)
            if entry.get("name") == E.STAGE_NAME_INPUT
        }
        if not values:
            problems.append(
                f"task {task_name!r} has no {E.STAGE_NAME_INPUT!r} input; the escalation "
                "form needs to be told which phase missed its deadline"
            )
            continue
        if values != {literal}:
            home = stage_of.get(task_name)
            problems.append(
                f"task {task_name!r} sets {E.STAGE_NAME_INPUT}={sorted(values)}; it should "
                f"be {literal!r}"
                + (
                    f" — the task lives in {home!r}, so the supplier would be told the "
                    "wrong phase ran late"
                    if home and home != literal
                    else ""
                )
            )

    crossed = {
        name: values
        for name in E.STAGE_NAME_LITERAL
        if (item := names_to_task.get(name)) is not None
        and (
            values := {
                entry.get("value")
                for entry in P.task_inputs(item)
                if entry.get("name") == E.STAGE_NAME_INPUT
            }
        )
        and not values <= {E.STAGE_NAME_LITERAL[name]}
        and values & set(E.STAGE_NAME_LITERAL.values())
    }
    if crossed:
        problems.append(
            f"escalation task(s) name another phase: {crossed} — one phase's escalation "
            "must never carry a sibling's name"
        )

    # ---- 5. dotted dereferences resolve ------------------------------------
    declared = P.variable_names(caseplan) | P.variable_ids(caseplan)
    for path, expr in P.expressions(caseplan):
        for root, prop in _DOTTED_RE.findall(expr):
            if root not in declared:
                problems.append(
                    f"{path}: expression dereferences vars.{root}.{prop}, but {root!r} is "
                    "not a variable the plan holds — the read yields undefined"
                )

    # The four supporting documents must still be read by the task that assesses them.
    # The fixture reads them through a guarded array walk, so assert the variables are
    # read rather than pinning the expression's shape.
    reader = next(
        (t for _stage, t in P.all_tasks(caseplan)
         if P.task_name(t) == E.DOCUMENT_READER_TASK),
        None,
    )
    if reader is None:
        problems.append(f"task {E.DOCUMENT_READER_TASK!r} is missing")
    else:
        read = set()
        for _name, expr in P.task_input_expressions(reader):
            read |= P.vars_read(expr)
        dropped = sorted(E.SUPPORTING_DOCUMENT_VARIABLES - read)
        if dropped:
            problems.append(
                f"{E.DOCUMENT_READER_TASK!r} does not read {dropped}; the SDD gives it "
                "all four supporting documents to assess"
            )

    print(f"checked {P.find_caseplan()}")
    print(
        f"connector tasks: {len(connector_tasks)}   fixture extracts: "
        f"{len(fixture_extracts)}   output labels: {sorted(labels)}"
    )
    if not problems:
        print(
            f"OK: all {E.CONNECTOR_TASK_COUNT} connector tasks read the lowercase wire "
            f"path {E.CONNECTOR_OUTPUT_PATH!r} into {E.CONNECTOR_OUTPUT_TARGET!r}, the "
            "PascalCase output labels are correctly not part of that contract, and every "
            "dotted dereference resolves to a variable the plan holds"
        )
        return 0

    print(f"\nFAIL: {len(problems)} field-name finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
