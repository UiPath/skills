#!/usr/bin/env python3
"""SupplierOnboarding: did the case variables keep the type and default the SDD gave them?

Six assertions. `uip maestro case validate` accepts every failure below, and four of
the six survive into a plan that opens and runs, faulting only when a route first
reads the slot.

 1. Every Case Variables row reaches the plan, in the group its Category selects.
    A `Variable` row lands in `inputOutputs`, an `In` row in both `inputs` and
    `inputOutputs`, an `Out` row in both `outputs` and `inputOutputs`.
 2. Each one keeps the SDD's declared `type`. A `double` written as `string` compares
    as text, so 90000 sorts above 500000 and the sign-off tier inverts.
 3. A `default` is present exactly where the skill's per-category shape puts one: on
    an `In` row's formal slot, on an `Out` row's companion, and on a `Variable` row's
    companion when the SDD gives that row a Default. An `In` companion and an `Out`
    formal slot carry none.
 4. Wherever a `default` is written it is a JSON string, whatever the variable's type.
    A number, a boolean, an object or an array there is deleted on the way to BPMN,
    and the slot then starts undefined instead of at its default. Every `file`
    variable defaults to the empty string.
 5. A variable the SDD gives a Default carries that same value.
 6. A `Variable` row is marked `custom: true`; an `In` row's companion is not. The
    flag is what separates case state from a trigger argument.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402

PRIMITIVE_DEFAULT = "`default` is a JSON string on every type"


def _by_name(plan: dict) -> dict[str, dict[str, dict]]:
    groups = P.variables(plan)
    return {g: {e.get("name"): e for e in (groups.get(g) or [])} for g in
            ("inputs", "outputs", "inputOutputs")}


def main() -> int:
    facts = E.sdd_facts()
    plan = P.load()
    found = _by_name(plan)
    problems: list[str] = []

    for name, (category, vtype, default) in sorted(facts["variables"].items()):
        group = E.VAR_GROUP[category]
        # An In row and an Out row each own a formal slot plus a companion; a pure
        # Variable row owns only the companion.
        wanted = {group} | ({"inputOutputs"} if category != "Variable" else set())

        missing = sorted(g for g in wanted if name not in found[g])
        if missing:
            problems.append(
                f"variable {name!r} (Category {category}) is missing from {missing}; "
                f"a route that reads it gets nothing and the read faults"
            )
            continue

        for g in sorted(wanted):
            entry = found[g][name]

            actual_type = entry.get("type")
            if actual_type != vtype:
                problems.append(
                    f"variable {name!r} in {g} has type {actual_type!r}; the SDD "
                    f"declares {vtype!r}"
                )

            # Which slots carry a `default` is fixed per category by the skill's
            # shape table. An `In` companion and an `Out` formal slot carry none, and
            # a `Variable` companion carries one only when the SDD sets a Default.
            wants_default = (
                (category == "In" and g == "inputs")
                or (category == "Out" and g == "inputOutputs")
                or (category == "Variable" and bool(default))
            )
            if "default" not in entry:
                if wants_default:
                    problems.append(
                        f"variable {name!r} in {g} carries no `default`; its SDD row "
                        f"gives it {default!r}"
                    )
                continue
            if not wants_default and category != "Variable":
                problems.append(
                    f"variable {name!r} in {g} carries a `default`; that slot holds "
                    f"none for a Category {category} row"
                )
                continue

            value = entry["default"]
            if not isinstance(value, str):
                problems.append(
                    f"variable {name!r} in {g} has a {type(value).__name__} default "
                    f"{value!r}; {PRIMITIVE_DEFAULT}, and a non-string one is dropped "
                    f"silently on the way to BPMN"
                )
                continue

            if vtype == "file" and value != "":
                problems.append(
                    f"file variable {name!r} in {g} defaults to {value!r}; a file "
                    f"default must be the empty string"
                )

            if default and value != default:
                problems.append(
                    f"variable {name!r} in {g} defaults to {value!r}; the SDD gives "
                    f"it {default!r}"
                )

        companion = found["inputOutputs"][name]
        is_custom = companion.get("custom") is True
        if category == "Variable" and not is_custom:
            problems.append(
                f"variable {name!r} is case state and is not marked `custom: true`"
            )
        if category == "In" and is_custom:
            problems.append(
                f"variable {name!r} is a trigger argument and is marked "
                f"`custom: true`, which reads it as case state"
            )

    if not problems:
        counts = {}
        for category, _t, _d in facts["variables"].values():
            counts[category] = counts.get(category, 0) + 1
        print(f"checked {P.find_caseplan()}")
        print(
            f"OK: all {len(facts['variables'])} case variables "
            f"({counts.get('In', 0)} In, {counts.get('Variable', 0)} Variable, "
            f"{counts.get('Out', 0)} Out) reach the plan in the right group, keep the "
            f"SDD's type and Default, carry a string `default`, and every file slot "
            f"defaults empty"
        )
        return 0

    print(f"\nFAIL: {len(problems)} variable finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
