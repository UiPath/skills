#!/usr/bin/env python3
"""A `=` output that reads another output's var must sit after that output.

The engine evaluates a task's `data.outputs` in array order and writes each result
into the variable scope before evaluating the next, so a row reads only what
precedes it. A computed row placed first gets the case variable's default on every
run, and `uip maestro case validate` reports `Valid` either way.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import find_caseplan  # noqa: E402

VARS_READS = (
    re.compile(r"\bvars\.([A-Za-z_$][A-Za-z0-9_$]*)"),
    re.compile(r"\bvars\s*\[\s*[\"']([A-Za-z_$][A-Za-z0-9_$]*)[\"']\s*\]"),
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def names_read(expression: str) -> set[str]:
    """Every `vars.<name>` an expression reads, whole identifiers only."""
    found: set[str] = set()
    for pattern in VARS_READS:
        found.update(m.group(1) for m in pattern.finditer(expression))
    return found


def outputs_of(task: dict) -> list[dict]:
    return [o for o in (task.get("data") or {}).get("outputs") or [] if isinstance(o, dict)]


def all_tasks(plan: dict):
    for node in plan.get("nodes") or []:
        for column in (node.get("data") or {}).get("tasks") or []:
            for task in column or []:
                if isinstance(task, dict):
                    yield node, task


def main() -> None:
    with open(find_caseplan()) as fh:
        plan = json.load(fh)

    decision_rows = []
    problems = []

    for node, task in all_tasks(plan):
        outs = outputs_of(task)
        # First writer owns the position: a row reading its own var is the
        # self-reference defect, which `--strict` reports separately.
        written_at: dict[str, int] = {}
        for index, out in enumerate(outs):
            var = out.get("var")
            if isinstance(var, str) and var and var not in written_at:
                written_at[var] = index

        for index, out in enumerate(outs):
            label = out.get("name") or f"#{index}"
            if out.get("var") == "reviewerDecision":
                decision_rows.append((task.get("id"), index, out))
            # `value` and `source` carry the same expression on these rows, so
            # report the row once and name the field the read was found in.
            reported = False
            for field in ("value", "source"):
                if reported:
                    break
                expr = out.get(field)
                if not isinstance(expr, str) or not expr.startswith("="):
                    continue
                for name in sorted(names_read(expr)):
                    at = written_at.get(name)
                    if at is None or at <= index:
                        continue
                    problems.append(
                        f'task {task.get("id")} output "{label}" at index {index} reads '
                        f'vars.{name} in {field}={expr!r}, and the output writing '
                        f'"{name}" is at index {at}. The engine evaluates outputs in '
                        f'array order and writes each one before the next, so this '
                        f'reads the case variable default. Move "{label}" after index {at}.'
                    )
                    reported = True
                    break

    if problems:
        fail(f"{len(problems)} output(s) read a later sibling:\n  - " + "\n  - ".join(problems))

    # The task the prompt asked for has to exist, or the check above passed on an
    # empty file rather than on a correct one.
    if not decision_rows:
        fail(
            'no output writes "reviewerDecision". The SDD row '
            '`reviewerDecision = =js:vars.$xref(...,\'Action\')` was not wired, so the '
            "ordering rule was never exercised."
        )

    for task_id, index, out in decision_rows:
        reads = set()
        for field in ("value", "source"):
            expr = out.get(field)
            if isinstance(expr, str):
                reads |= names_read(expr)
        if not reads:
            fail(
                f'task {task_id}: the "reviewerDecision" output at index {index} reads no '
                f"vars.<name>; its value is {out.get('value')!r}. The SDD computes it from "
                "the task's own Action slot, so it has to read that slot."
            )

    print(
        f"OK: {len(decision_rows)} reviewerDecision row(s) wired, "
        "every output reads only outputs that precede it"
    )


if __name__ == "__main__":
    main()
