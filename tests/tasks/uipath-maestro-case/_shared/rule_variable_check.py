#!/usr/bin/env python3
"""Rule + variable mapping integrity check for a generated caseplan.json.

Goes beyond `uip maestro case validate` (which is schema-shape only) and
asserts semantic correctness against the V20 contract defined in
`cli/packages/case-tool/src/types/case-management.types.ts`:

Rule mapping (per stage entry/exit, per task entry, per case-exit):
  - Every rule has a `rule` field whose value is in the V12 enum
  - Deprecated V11-era rule names (`condition`, `stage-complete`, `timer`)
    do NOT appear in V20 output
  - `selected-stage-completed` / `selected-stage-exited` reference an
    existing stage id in `plan.nodes`
  - `selected-tasks-completed.selectedTasksIds[]` all reference real task
    ids found anywhere in `stage.data.tasks`
  - Stage `exitConditions[].exitToStageId` points to a real stage id
  - Stage `exitConditions[].type` is one of the V20 enum values

Variable mapping:
  - Every UiPathVariable in `plan.variables.{inputs, outputs, inputOutputs}`
    has both `name` and `type`
  - No duplicate variable ids
  - Every `=vars.<id>` reference (in conditionExpressions, task data,
    expressions) resolves to a global variable id
  - Every `=bindings.<id>` reference resolves to an entry in `plan.bindings[]`
  - Task `data.inputs[].var` / `data.outputs[].var` / `data.context[].var`
    references resolve to a global variable id when present
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_check import (  # noqa: E402
    find_stages,
    get_bindings,
    get_case_exit_conditions,
    get_variables,
    iter_tasks,
    read_caseplan,
)


V12_RULES = {
    "wait-for-connector",
    "case-entered",
    "selected-stage-completed",
    "selected-stage-exited",
    "selected-tasks-completed",
    "current-stage-entered",
    "adhoc",
    "required-stages-completed",
    "required-tasks-completed",
    "user-selected-stage",
    "runs-sequentially",
}

DEPRECATED_RULES = {"condition", "stage-complete", "timer"}

EXIT_TYPES = {"exit-only", "wait-for-user", "return-to-origin"}

# Per-scope rule allow-lists — sourced verbatim from
# cli/packages/case-tool/src/utils/schema-helpers.ts (VALID_*_RULE_TYPES).
# A rule appearing in the wrong scope is a logical bug even if the schema
# round-trips: e.g. `required-stages-completed` only makes sense at case
# completion, never at a stage entry.
SCOPE_ALLOWED: dict[str, set[str]] = {
    "stage-entry": {
        "case-entered",
        "selected-stage-exited",
        "selected-stage-completed",
        "wait-for-connector",
        "user-selected-stage",
    },
    "stage-completion": {
        "required-tasks-completed",
        "wait-for-connector",
    },
    "stage-exit": {
        "selected-tasks-completed",
        "wait-for-connector",
    },
    "task-entry": {
        "current-stage-entered",
        "selected-tasks-completed",
        "wait-for-connector",
        "adhoc",
        "runs-sequentially",
    },
    "case-completion": {
        "required-stages-completed",
        "wait-for-connector",
    },
    "case-exit": {
        "selected-stage-completed",
        "selected-stage-exited",
        "wait-for-connector",
    },
}

VARS_REF = re.compile(r"=vars\.([A-Za-z0-9_\-]+)")
BIND_REF = re.compile(r"=bindings\.([A-Za-z0-9_\-]+)")


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _iter_rules_from_condition(cond: dict) -> Iterable[dict]:
    for group in cond.get("rules") or []:
        for rule in group or []:
            if isinstance(rule, dict):
                yield rule


def _iter_all_conditions(plan: dict):
    """Yield (scope, owner_label, condition_dict) for every condition site.

    Stage exitConditions split into 'stage-completion' (marksStageComplete=true)
    vs 'stage-exit' (false / missing). Case exits split into 'case-completion'
    (marksCaseComplete=true) vs 'case-exit' (false). The CLI's
    VALID_*_RULE_TYPES allow-lists are scope-distinct, so the same physical
    array must be classified before checking rule legality.
    """
    for stage in find_stages(plan, include_exception=True):
        label = (stage.get("data") or {}).get("label") or stage.get("id", "?")
        data = stage.get("data") or {}
        for c in data.get("entryConditions") or []:
            yield ("stage-entry", label, c)
        for c in data.get("exitConditions") or []:
            scope = "stage-completion" if c.get("marksStageComplete") else "stage-exit"
            yield (scope, label, c)
        for task in iter_tasks({"nodes": [stage]}):
            tlabel = task.get("displayName") or task.get("id", "?")
            for c in task.get("entryConditions") or []:
                yield ("task-entry", f"{label}::{tlabel}", c)
    for c in get_case_exit_conditions(plan):
        scope = "case-completion" if c.get("marksCaseComplete") else "case-exit"
        yield (scope, "<case>", c)


def _all_task_ids(plan: dict) -> set[str]:
    out: set[str] = set()
    for t in iter_tasks(plan):
        tid = t.get("id") or t.get("elementId")
        if tid:
            out.add(tid)
    return out


def _all_stage_ids(plan: dict) -> set[str]:
    return {s["id"] for s in find_stages(plan, include_exception=True) if s.get("id")}


def _all_variable_ids(plan: dict) -> set[str]:
    out: set[str] = set()
    vars_ = get_variables(plan)
    for section in ("inputs", "outputs", "inputOutputs"):
        for v in vars_.get(section) or []:
            for key in ("id", "canonicalId", "camelizedId", "name"):
                val = v.get(key)
                if isinstance(val, str) and val:
                    out.add(val)
    return out


def _all_binding_ids(plan: dict) -> set[str]:
    return {b.get("id") for b in get_bindings(plan) if b.get("id")}


def _stringify_for_refs(obj) -> str:
    return json.dumps(obj, default=str)


def check_rule_mapping(plan: dict) -> list[str]:
    issues: list[str] = []
    stage_ids = _all_stage_ids(plan)
    task_ids = _all_task_ids(plan)

    for scope, owner, cond in _iter_all_conditions(plan):
        for rule in _iter_rules_from_condition(cond):
            rname = rule.get("rule")
            if not rname:
                issues.append(f"[{scope}] {owner}: rule missing `rule` field")
                continue
            if rname in DEPRECATED_RULES:
                issues.append(
                    f"[{scope}] {owner}: deprecated V11 rule {rname!r} "
                    f"present in V20 output"
                )
                continue
            if rname not in V12_RULES:
                issues.append(
                    f"[{scope}] {owner}: unknown rule {rname!r}; "
                    f"expected one of {sorted(V12_RULES)}"
                )
                continue
            allowed_here = SCOPE_ALLOWED.get(scope, V12_RULES)
            if rname not in allowed_here:
                issues.append(
                    f"[{scope}] {owner}: rule {rname!r} not allowed at this "
                    f"scope; allowed for {scope}: {sorted(allowed_here)}"
                )
                continue
            if rname in ("selected-stage-completed", "selected-stage-exited"):
                sid = rule.get("selectedStageId")
                if sid and sid not in stage_ids:
                    issues.append(
                        f"[{scope}] {owner}: {rname} selectedStageId={sid!r} "
                        f"does not match any stage id"
                    )
            if rname == "selected-tasks-completed":
                for tid in rule.get("selectedTasksIds") or []:
                    if tid not in task_ids:
                        issues.append(
                            f"[{scope}] {owner}: selected-tasks-completed "
                            f"references unknown task id {tid!r}"
                        )

        if scope in ("stage-exit", "stage-completion"):
            et = cond.get("type")
            if et is not None and et not in EXIT_TYPES:
                issues.append(
                    f"[{scope}] {owner}: type={et!r}; expected one of "
                    f"{sorted(EXIT_TYPES)}"
                )
            tgt = cond.get("exitToStageId")
            if tgt and tgt not in stage_ids:
                issues.append(
                    f"[{scope}] {owner}: exitToStageId={tgt!r} does not "
                    f"match any stage id"
                )

    return issues


def check_variable_mapping(plan: dict) -> list[str]:
    issues: list[str] = []
    vars_ = get_variables(plan)
    seen_ids: dict[str, str] = {}
    for section in ("inputs", "outputs", "inputOutputs"):
        for v in vars_.get(section) or []:
            name = v.get("name")
            vtype = v.get("type")
            if not name:
                issues.append(f"global {section} var missing `name`: {v}")
            if not vtype:
                issues.append(f"global {section} var {name!r} missing `type`")
            vid = v.get("id")
            if vid:
                if vid in seen_ids:
                    issues.append(
                        f"duplicate global variable id {vid!r} "
                        f"(also used by {seen_ids[vid]!r})"
                    )
                seen_ids[vid] = name or "<anon>"

    valid_var_ids = _all_variable_ids(plan)
    valid_bind_ids = _all_binding_ids(plan)

    text = _stringify_for_refs(plan)
    for ref in set(VARS_REF.findall(text)):
        if ref not in valid_var_ids:
            issues.append(
                f"=vars.{ref} referenced but no global variable with id / "
                f"canonicalId / name {ref!r}"
            )
    for ref in set(BIND_REF.findall(text)):
        if ref not in valid_bind_ids:
            issues.append(f"=bindings.{ref} referenced but no binding with id {ref!r}")

    for task in iter_tasks(plan):
        tlabel = task.get("displayName") or task.get("id", "?")
        data = task.get("data") or {}
        for section in ("inputs", "outputs", "context"):
            for v in data.get(section) or []:
                if not isinstance(v, dict):
                    continue
                if not v.get("name"):
                    issues.append(
                        f"task {tlabel!r} {section} entry missing `name`: {v}"
                    )
                if not v.get("type"):
                    issues.append(
                        f"task {tlabel!r} {section}.{v.get('name', '?')} "
                        f"missing `type`"
                    )
                ref = v.get("var")
                if isinstance(ref, str) and ref and ref not in valid_var_ids:
                    issues.append(
                        f"task {tlabel!r} {section}.{v.get('name', '?')}.var "
                        f"= {ref!r} does not resolve to a global variable"
                    )

    return issues


def main():
    plan = read_caseplan()
    rule_issues = check_rule_mapping(plan)
    var_issues = check_variable_mapping(plan)

    if rule_issues or var_issues:
        lines = ["FAIL: rule + variable mapping integrity"]
        if rule_issues:
            lines.append(f"  rule issues ({len(rule_issues)}):")
            lines.extend(f"    - {m}" for m in rule_issues[:25])
            if len(rule_issues) > 25:
                lines.append(f"    ... and {len(rule_issues) - 25} more")
        if var_issues:
            lines.append(f"  variable issues ({len(var_issues)}):")
            lines.extend(f"    - {m}" for m in var_issues[:25])
            if len(var_issues) > 25:
                lines.append(f"    ... and {len(var_issues) - 25} more")
        sys.exit("\n".join(lines))

    n_rules = sum(
        1
        for _ in (
            r
            for _, _, c in _iter_all_conditions(plan)
            for r in _iter_rules_from_condition(c)
        )
    )
    n_vars = sum(
        len(get_variables(plan).get(k) or [])
        for k in ("inputs", "outputs", "inputOutputs")
    )
    n_binds = len(get_bindings(plan))
    print(
        f"OK: rule mapping clean ({n_rules} rules across all condition sites, "
        f"all V12 names, all selectedStage/Task references resolve); "
        f"variable mapping clean ({n_vars} global variables, {n_binds} "
        f"bindings, all =vars / =bindings references resolve)"
    )


if __name__ == "__main__":
    main()
