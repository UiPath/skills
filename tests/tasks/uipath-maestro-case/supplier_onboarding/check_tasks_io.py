#!/usr/bin/env python3
"""SupplierOnboarding: are the right tasks bound to the right resources, wired right?

Seven assertions.

 1. Twenty-one tasks in the declared per-stage sets, each of the declared type. A
    task built as the wrong class runs on the wrong runtime.
 2. All fourteen tenant resource identities are bound, none repeated or missing,
    and no task is left a skeleton.
 3. Every task output lands in a slot the plan declares. An output written nowhere
    means the next task reads empty.
 4. The expression-recipient task carries `data.recipient` as the object
    `{Type: 3, Value: "=vars.assignedBuyerEmail"}`. **`uip maestro case validate`
    does not check `data.recipient` at all** — a bare string, or a dropped field,
    passes validation and then the task reaches nobody. The role-assigned tasks are
    not required to carry one: the skill's own references disagree on whether a
    role becomes `Type 1` or no recipient at all, so a grader must not pick a side.
    It can still reject the one shape both readings rule out: a role name sitting
    in `Type 2`, which is the email type, so the platform reads "Procurement
    Operations Lead" as a literal mailbox and the task reaches nobody.
 5. ERP registration and the child case run only once. A re-entered setup phase
    would otherwise mint a second supplier record.
 6. The child case does not block the parent.
 7. The on-demand task lives in exactly one stage, its own.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402
from _shared.case_check import task_is_skeleton  # noqa: E402

def main() -> int:
    E.sdd_facts()
    caseplan = P.load()
    problems: list[str] = []

    by_label = P.stages_by_label(caseplan)

    # ---- 1. task inventory --------------------------------------------------
    total = 0
    for label, rows in sorted(E.STAGE_TASKS.items()):
        node = by_label.get(label)
        if node is None:
            continue
        actual = P.tasks(node)
        total += len(actual)
        by_name = {P.task_name(t): t for t in actual}
        for name, ttype, required, once in rows:
            task = by_name.get(name)
            if task is None:
                problems.append(f"stage {label!r} is missing task {name!r}")
                continue
            if P.task_type(task) != ttype:
                problems.append(
                    f"task {name!r} is type {P.task_type(task)!r}; the SDD makes it "
                    f"{ttype!r} — a different class runs on a different runtime"
                )
            if bool(task.get("isRequired")) != required:
                problems.append(
                    f"task {name!r} isRequired={bool(task.get('isRequired'))}; the SDD "
                    f"says {required}"
                    + (
                        " — a required escalation task stops the stage completing unless "
                        "the phase breached"
                        if not required
                        else ""
                    )
                )
            if bool(task.get("shouldRunOnlyOnce")) != once:
                problems.append(
                    f"task {name!r} shouldRunOnlyOnce="
                    f"{bool(task.get('shouldRunOnlyOnce'))}; the SDD says {once}"
                )
        unexpected = sorted(set(by_name) - {name for name, *_ in rows})
        if unexpected:
            problems.append(f"stage {label!r} carries extra task(s) {unexpected}")

    if total != E.TOTAL_TASKS:
        problems.append(f"{total} tasks in the plan; the SDD declares {E.TOTAL_TASKS}")

    types = Counter(P.task_type(t) for _stage, t in P.all_tasks(caseplan))
    if types != Counter(E.TASK_TYPE_COUNTS):
        problems.append(
            f"task-type counts are {dict(sorted(types.items()))}; the SDD declares "
            f"{dict(sorted(E.TASK_TYPE_COUNTS.items()))}"
        )

    # ---- 2. resources -------------------------------------------------------
    found = P.resource_keys(caseplan)
    missing = sorted(set(E.RESOURCE_KEYS) - found)
    extra = sorted(found - set(E.RESOURCE_KEYS))
    if missing:
        problems.append(
            f"{len(missing)} resource(s) the SDD names are bound nowhere in the plan: "
            f"{missing}"
        )
    if extra:
        problems.append(
            f"the plan binds resource(s) the SDD does not name: {extra}"
        )

    skeletons = [
        f"{stage}/{P.task_name(t)}"
        for stage, t in P.all_tasks(caseplan)
        if task_is_skeleton(t)
    ]
    if skeletons:
        problems.append(
            f"{len(skeletons)} task(s) are skeletons — every resource in this SDD is "
            f"deployed, so none should be unresolved: {skeletons}"
        )

    # ---- 3. every declared output target is actually written ---------------
    writers: dict[str, set[str]] = {}
    for _stage, task in P.all_tasks(caseplan):
        for target in P.output_targets(task):
            writers.setdefault(target, set()).add(P.task_name(task))

    declared = P.variable_names(caseplan) | P.variable_ids(caseplan)
    for target, expected_tasks in sorted(E.OUTPUT_TARGETS.items()):
        if target not in declared:
            problems.append(
                f"variable {target!r} is not declared in the plan; the SDD has "
                f"{expected_tasks} write to it"
            )
        actual = writers.get(target, set())
        if not actual:
            problems.append(
                f"nothing in the plan writes {target!r}; the SDD assigns it to "
                f"{expected_tasks} — every task that reads it gets nothing"
            )
            continue
        dropped = sorted(set(expected_tasks) - actual)
        if dropped:
            problems.append(
                f"task(s) {dropped} do not write {target!r}; the SDD's Output table gives "
                f"them that reassign. Written instead by {sorted(actual)}"
            )

    # ---- 4. expression recipients ------------------------------------------
    names_to_task = {P.task_name(t): t for _s, t in P.all_tasks(caseplan)}
    for name in sorted(E.EXPRESSION_RECIPIENT_TASKS):
        task = names_to_task.get(name)
        if task is None:
            continue
        recipient = P.task_data(task).get("recipient")
        if recipient is None:
            problems.append(
                f"task {name!r} has no `data.recipient`; the SDD routes it to the buyer the "
                "intake lookup returned. `validate` does not check this field, so a dropped "
                "recipient passes the build and the task reaches nobody"
            )
            continue
        if not isinstance(recipient, dict):
            problems.append(
                f"task {name!r} `data.recipient` is {type(recipient).__name__} "
                f"{recipient!r}; it must be the object {{Type, Value}} — Studio Web's canvas "
                "fails silently on any other shape and `validate` misses it"
            )
            continue
        rtype = recipient.get("Type", recipient.get("type"))
        rvalue = recipient.get("Value", recipient.get("value"))
        if rtype != E.EXPRESSION_RECIPIENT_TYPE:
            problems.append(
                f"task {name!r} recipient Type is {rtype!r}; an expression recipient is "
                f"Type {E.EXPRESSION_RECIPIENT_TYPE}"
            )
        if rvalue != E.EXPRESSION_RECIPIENT_VALUE:
            problems.append(
                f"task {name!r} recipient Value is {rvalue!r}; the SDD binds "
                f"{E.EXPRESSION_RECIPIENT_VALUE!r}"
            )

    # A role recipient may be omitted or carry a group id; both readings of the skill's
    # references are defensible and neither is asserted. What neither allows is the role's
    # display name in Type 2, the email type, which sends the task to a mailbox of that name.
    for _stage, task in P.all_tasks(caseplan):
        recipient = P.task_data(task).get("recipient")
        if not isinstance(recipient, dict):
            continue
        value = recipient.get("Value", recipient.get("value"))
        rtype = recipient.get("Type", recipient.get("type"))
        if rtype != E.EMAIL_RECIPIENT_TYPE or not isinstance(value, str):
            continue
        if "@" not in value:
            problems.append(
                f"task {task.get('displayName')!r} recipient is Type {E.EMAIL_RECIPIENT_TYPE} "
                f"(email) with value {value!r}, which is a role name, not an address; a role is "
                f"either omitted or carried as a group id, never as a mailbox"
            )

    # `data.inputs` is a binding map, not a place to restate the receiving contract. A `required`
    # flag here compiles into the dispatch's own `uipath:inputSchema` required array, which the
    # runtime checks before the job starts, so a bound value that resolves empty fails the job
    # rather than reaching it. Where a caller must supply a value belongs in entry-points.json.
    restated = sorted({
        f"{task.get('displayName')}.{i.get('name')}"
        for _s, task in P.all_tasks(caseplan)
        for i in P.task_inputs(task)
        if i.get("required") is True
    })
    if restated:
        problems.append(
            f"{len(restated)} task input(s) restate the resource's own contract with "
            f"`required: true`: {restated[:4]}. That compiles into a second gate the runtime "
            f"checks before the job starts, and an empty bound value then fails the job"
        )

    # ---- 5 + 6. the child case and the ERP write ---------------------------
    for name in sorted(E.RUN_ONCE_TASKS):
        task = names_to_task.get(name)
        if task is not None and not bool(task.get("shouldRunOnlyOnce")):
            problems.append(
                f"task {name!r} is not run-once; a re-entered stage would run it twice"
            )

    child = names_to_task.get(E.CHILD_CASE_TASK)
    if child is None:
        problems.append(f"task {E.CHILD_CASE_TASK!r} is missing")
    else:
        data = P.task_data(child)
        waits = data.get("waitForCompletion")
        if waits is None:
            waits = data.get("waitForChildCase")
        if bool(waits) != E.CHILD_CASE_WAITS:
            problems.append(
                f"{E.CHILD_CASE_TASK!r} waitForCompletion={waits!r}; the SDD does not wait "
                "— the negotiation must not hold up the application"
            )

    # ---- 7. on-demand tasks stay in their own stage ------------------------
    for name, home in sorted(E.ADHOC_TASKS.items()):
        homes = sorted(
            stage for stage, task in P.all_tasks(caseplan) if P.task_name(task) == name
        )
        if homes != [home]:
            problems.append(
                f"on-demand task {name!r} appears in {homes}; the source restricts it to "
                f"{home!r}"
            )
        task = names_to_task.get(name)
        if task is not None:
            rules = {n for c in P.task_entry_conditions(task) for n in P.rule_names(c)}
            if "adhoc" not in rules:
                problems.append(
                    f"on-demand task {name!r} entry rules are {sorted(rules)}; a manually "
                    "launched task needs its own `adhoc` rule"
                )

    print(f"checked {P.find_caseplan()}")
    print(f"tasks: {total}  types: {dict(sorted(types.items()))}")
    print(f"resource keys bound: {len(found)}/{len(E.RESOURCE_KEYS)}")
    if not problems:
        print(
            f"OK: {E.TOTAL_TASKS} tasks in their declared stages and classes, all "
            f"{len(E.RESOURCE_KEYS)} resource keys bound with no skeletons, every "
            "output landing in a declared slot, the expression recipient carrying "
            f"the {{Type,Value}} object, {len(E.RUN_ONCE_TASKS)} run-once tasks, a "
            f"non-blocking child case, and {len(E.ADHOC_TASKS)} on-demand task locked to its own stage"
        )
        return 0

    print(f"\nFAIL: {len(problems)} task/IO finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
