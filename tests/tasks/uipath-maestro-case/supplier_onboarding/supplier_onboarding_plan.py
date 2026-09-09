"""Caseplan accessors shared by the SupplierOnboarding graders.

Everything here is read-only and tolerant of the authoring freedom the skill
allows (display-name punctuation, which encoding a stage hop uses, whether a
guard sits on the condition or on its rule). Structural facts the skill pins
are asserted by the graders, not here.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Iterable, Iterator, NoReturn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    find_stages,
    find_triggers,
    get_case_exit_conditions,
    get_variables,
    read_caseplan,
    stage_transitions,
)

from supplier_onboarding_expected import CASEPLAN_PATH, norm, norm_expr  # noqa: E402

__all__ = [
    "fail",
    "find_stages",
    "find_triggers",
    "get_case_exit_conditions",
    "get_variables",
    "stage_transitions",
    "load_plan",
    "stage_of",
    "stage_label",
    "tasks_of",
    "task_names",
    "find_task",
    "task_index",
    "iter_rules",
    "rule_names",
    "condition_expressions",
    "has_expression",
    "binding_value",
]


def fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def load_plan() -> dict:
    path = CASEPLAN_PATH if os.path.isfile(CASEPLAN_PATH) else None
    if path is None:
        found = find_caseplan()
        fail(
            f"expected the generated caseplan at {CASEPLAN_PATH}; "
            f"found {found} instead"
        )
    return read_caseplan(path)


def stage_label(stage: dict) -> str:
    return (stage.get("data") or {}).get("label") or stage.get("id") or "<unnamed>"


def stage_of(plan: dict, label: str) -> dict:
    wanted = norm(label)
    for stage in find_stages(plan, include_exception=True):
        if norm(stage_label(stage)) == wanted:
            return stage
    present = [stage_label(s) for s in find_stages(plan, include_exception=True)]
    fail(f"stage {label!r} not found; stages present: {present}")


def tasks_of(stage: dict) -> list[dict]:
    out: list[dict] = []
    for lane in (stage.get("data") or {}).get("tasks") or []:
        if isinstance(lane, dict):      # mis-nested flat task
            out.append(lane)
        elif isinstance(lane, list):
            out.extend(task for task in lane if isinstance(task, dict))
    return out


def binding_value(plan: dict, reference: object) -> str | None:
    """Resolve a ``=bindings.<id>`` reference to its binding default."""
    value = reference
    seen: set[str] = set()
    bindings = {b.get("id"): b for b in plan.get("bindings") or []}
    while isinstance(value, str) and value.startswith("=bindings."):
        binding_id = value.removeprefix("=bindings.").split(".", 1)[0]
        if binding_id in seen:
            return None
        seen.add(binding_id)
        binding = bindings.get(binding_id)
        if not binding:
            return None
        value = binding.get("default") or binding.get("resourceKey")
    return value if isinstance(value, str) else None


def task_names(plan: dict, task: dict) -> set[str]:
    data = task.get("data") or {}
    candidates = {
        task.get("displayName"),
        task.get("label"),
        data.get("displayName"),
        data.get("label"),
        binding_value(plan, data.get("name")),
    }
    return {norm(c) for c in candidates if isinstance(c, str) and c}


def find_task(plan: dict, stage: dict, name: str) -> dict | None:
    wanted = norm(name)
    for task in tasks_of(stage):
        if wanted in task_names(plan, task):
            return task
    return None


def task_index(plan: dict) -> dict[str, dict]:
    """``{normalized task name: task}`` across every stage."""
    index: dict[str, dict] = {}
    for stage in find_stages(plan, include_exception=True):
        for task in tasks_of(stage):
            for name in task_names(plan, task):
                index.setdefault(name, task)
    return index


def iter_rules(conditions: Iterable[dict]) -> Iterator[dict]:
    for condition in conditions or []:
        for group in condition.get("rules") or []:
            for rule in group or []:
                if isinstance(rule, dict):
                    yield rule


def rule_names(conditions: Iterable[dict]) -> set[str]:
    return {rule.get("rule") for rule in iter_rules(conditions) if rule.get("rule")}


def condition_expressions(conditions: Iterable[dict]) -> set[str]:
    """Every normalized guard expression on the conditions or their rules."""
    out: set[str] = set()
    for condition in conditions or []:
        for holder in [condition, *iter_rules([condition])]:
            for key in ("conditionExpression", "expression"):
                value = holder.get(key)
                if isinstance(value, str) and value:
                    out.add(norm_expr(value))
    return out


def has_expression(conditions: Iterable[dict], expression: str) -> bool:
    wanted = norm_expr(expression)
    return any(wanted in seen for seen in condition_expressions(conditions))


def dump(value: object) -> str:
    return json.dumps(value, default=str)
