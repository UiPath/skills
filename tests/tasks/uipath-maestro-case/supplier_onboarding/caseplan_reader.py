#!/usr/bin/env python3
"""Read-only accessors over the built caseplan, shared by the five SupplierOnboarding graders.

One definition per field, deliberately. The emitted shape differed from the obvious
guess in nine places while the graders were written; a single definition is why each of
those nine was fixed once instead of five times.

Tolerant of the authoring freedom the skill allows: display-name punctuation, whether a
guard sits on the condition or on one of its rules, and which of the two legal
stage-hop encodings a transition uses. Facts the skill pins are asserted by the
graders, not smoothed over here.

Nothing here decides pass or fail. Each grader collects its own findings and reports.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    get_case_exit_conditions,
    get_sla_rules,
    get_variables,
    read_caseplan,
)

STAGE_NODE_TYPE = "case-management:Stage"


def load() -> dict:
    return read_caseplan(find_caseplan())


# --- stages -------------------------------------------------------------------


def stages(plan: dict) -> list[dict]:
    return [n for n in plan.get("nodes") or [] if n.get("type") == STAGE_NODE_TYPE]


def label(node: dict) -> str:
    return ((node.get("data") or {}).get("label") or "").strip()


def stages_by_label(plan: dict) -> dict[str, dict]:
    return {label(node): node for node in stages(plan)}


def stage_ids(plan: dict) -> dict[str, str]:
    return {label(node): node.get("id") for node in stages(plan)}


def is_secondary(node: dict) -> bool:
    return (node.get("data") or {}).get("stageType") == "secondary"


def entry_conditions(node: dict) -> list[dict]:
    return (node.get("data") or {}).get("entryConditions") or []


def exit_conditions(node: dict) -> list[dict]:
    return (node.get("data") or {}).get("exitConditions") or []


# --- tasks --------------------------------------------------------------------


def tasks(node: dict) -> list[dict]:
    """Flatten the nested `data.tasks` rows into one list, order preserved."""
    rows = (node.get("data") or {}).get("tasks") or []
    out = []
    for row in rows:
        out.extend(row if isinstance(row, list) else [row])
    return out


def task_name(task: dict) -> str:
    data = task.get("data") or {}
    return (data.get("displayName") or task.get("displayName") or "").strip()


def task_type(task: dict) -> str:
    return (task.get("type") or "").strip()


def task_data(task: dict) -> dict:
    return task.get("data") or {}


def task_entry_conditions(task: dict) -> list[dict]:
    return task.get("entryConditions") or []


def task_skip_condition(task: dict) -> str:
    """The task's skip guard.

    It lives at the task's top level, NOT under `data` — reading only `data` misses it
    and reports a threshold the plan does carry as missing.
    """
    for source in (task, task_data(task)):
        value = source.get("skipCondition")
        if isinstance(value, str) and value:
            return value
    return ""


def all_tasks(plan: dict):
    """Yield (stage label, task) for every task in the plan."""
    for node in stages(plan):
        for task in tasks(node):
            yield label(node), task


def task_ids(plan: dict) -> dict[str, str]:
    return {task_name(t): t.get("id") for _stage, t in all_tasks(plan)}


# --- conditions and rules -----------------------------------------------------


def rules(cond: dict) -> list[dict]:
    """Every rule in a condition, flattened across its OR-of-AND groups."""
    out = []
    for group in cond.get("rules") or []:
        out.extend(group if isinstance(group, list) else [group])
    return out


def rule_names(cond: dict) -> list[str]:
    return [str(r.get("rule") or "") for r in rules(cond)]


def condition_expression(cond: dict) -> str:
    """The guard on a condition, wherever the author put it.

    The skill accepts the expression on the condition itself or on one of its rules.
    Both mean the same thing at runtime, so both read the same here.
    """
    direct = cond.get("conditionExpression")
    if direct:
        return str(direct)
    for rule in rules(cond):
        expr = rule.get("conditionExpression")
        if expr:
            return str(expr)
    return ""


def selected_stage_ids(cond: dict) -> set[str]:
    """Stage ids a `selected-stage-completed` / `-exited` rule points at.

    Deliberately reads both spellings. The emitted key is the singular `selectedStageId`
    holding a bare string, but a build that writes the plural array instead would otherwise
    blank every routing assertion at once and report a topology that looks empty rather than
    wrong. `stage_selector_spellings` is what actually judges the spelling.
    """
    out = set()
    for rule in rules(cond):
        one = rule.get("selectedStageId")
        if one:
            out.add(one)
        for many in rule.get("selectedStageIds") or []:
            out.add(many)
    return out


def stage_selector_spellings(plan: dict) -> list[tuple]:
    """(rule id, key) for every stage selector, so a grader can judge the key itself.

    `uip maestro case validate` accepts the plural array and the case then faults on its very
    first rules evaluation, before any task opens: `CaseRulesEvaluatorNode`, error 400300,
    "Error evaluating expression in activity inputs". Nothing downstream runs, so no other
    assertion in this suite gets the chance to notice.
    """
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("rule") in ("selected-stage-completed", "selected-stage-exited"):
                for key in ("selectedStageId", "selectedStageIds"):
                    if key in node:
                        found.append((node.get("id"), key))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(plan)
    return found


def selected_task_ids(cond: dict) -> set[str]:
    """Task ids a `selected-tasks-completed` rule points at.

    The emitted key is `selectedTasksIds` — plural on BOTH words. Reading only
    `selectedTaskIds` matches nothing and every task-selector assertion silently
    passes (verified against a built plan: 11 rules, all spelled `selectedTasksIds`).
    """
    out = set()
    for rule in rules(cond):
        for key in ("selectedTasksIds", "selectedTaskIds", "selectedTaskId"):
            value = rule.get(key)
            if isinstance(value, str) and value:
                out.add(value)
            elif isinstance(value, list):
                out.update(v for v in value if isinstance(v, str))
    return out


def sla_ids_referenced(cond: dict) -> set[str]:
    """SLA ids an `sla-status-change` rule listens to.

    The rule names the SLA directly via `slaId` — it carries no stage reference at
    all (verified against a built plan: 5 rules, all `{id, rule, slaId}`). An
    assertion written against `selectedStageId` here can never fire.
    """
    out = set()
    for rule in sla_status_change_rules(cond):
        value = rule.get("slaId")
        if isinstance(value, str) and value:
            out.add(value)
    return out


def sla_ids_of(target: dict) -> set[str]:
    """The ids of the SLA rules declared on a plan root or stage node."""
    return {
        str(rule.get("id"))
        for rule in sla_rules(target)
        if rule.get("id")
    }


def exit_type(cond: dict) -> str:
    return str(cond.get("type") or "")


def marks_complete(cond: dict) -> bool:
    return bool(cond.get("marksStageComplete"))


# --- SLA ----------------------------------------------------------------------


def sla_rules(target: dict) -> list[dict]:
    """SLA rules on the plan root or on a stage node."""
    if target.get("type") == STAGE_NODE_TYPE:
        return (target.get("data") or {}).get("slaRules") or []
    return get_sla_rules(target)


def escalations(sla: dict) -> list[dict]:
    return sla.get("escalationRule") or []


def escalation_trigger(esc: dict) -> str:
    return str(((esc.get("triggerInfo") or {}).get("type")) or "")


def escalation_at_risk_percent(esc: dict):
    return (esc.get("triggerInfo") or {}).get("atRiskPercentage")


def escalation_action_type(esc: dict) -> str:
    return str(((esc.get("action") or {}).get("type")) or "")


def escalation_recipients(esc: dict) -> list[dict]:
    return ((esc.get("action") or {}).get("recipients")) or []


def sla_status_change_rules(cond: dict) -> list[dict]:
    return [r for r in rules(cond) if str(r.get("rule")) == "sla-status-change"]


# --- variables ----------------------------------------------------------------


def variables(plan: dict) -> dict:
    return get_variables(plan) or {}


def variable_names(plan: dict) -> set[str]:
    out = set()
    for group in (variables(plan) or {}).values():
        for var in group or []:
            name = var.get("name")
            if name:
                out.add(name)
    return out


def variable_ids(plan: dict) -> set[str]:
    out = set()
    for group in (variables(plan) or {}).values():
        for var in group or []:
            vid = var.get("id")
            if vid:
                out.add(vid)
    return out


def input_names(plan: dict) -> list[str]:
    return [v.get("name") for v in (variables(plan).get("inputs") or [])]


def output_names(plan: dict) -> list[str]:
    return [v.get("name") for v in (variables(plan).get("outputs") or [])]


# --- task I/O -----------------------------------------------------------------


def task_inputs(task: dict) -> list[dict]:
    return task_data(task).get("inputs") or []


def task_outputs(task: dict) -> list[dict]:
    return task_data(task).get("outputs") or []


def task_input_expressions(task: dict) -> list[tuple[str, str]]:
    """Every `=...` expression bound to any of a task's inputs, as (input name, expr).

    Where the expression sits depends on the task class: a non-connector task puts it
    in `value`, a connector task nests it inside `body` under the payload's own field
    path. Reading only `value` misses every connector binding.
    """
    found: list[tuple[str, str]] = []

    def walk(node, name):
        if isinstance(node, dict):
            for value in node.values():
                walk(value, name)
        elif isinstance(node, list):
            for value in node:
                walk(value, name)
        elif isinstance(node, str) and node.startswith("="):
            found.append((name, node))

    for entry in task_inputs(task):
        name = str(entry.get("name") or "")
        for key in ("value", "body"):
            if key in entry:
                walk(entry[key], name)
    return found



def activity_type_ids(task: dict) -> set[str]:
    """Every `uiPathActivityTypeId` a connector task carries.

    The id names which operation of the connector the task runs, and it sits several
    levels down inside `data.context[].body`, under a different parent per context
    entry. Walking for the key is what keeps this independent of that nesting.
    """
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "uiPathActivityTypeId" and isinstance(value, str) and value:
                    found.add(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk((task.get("data") or {}).get("context"))
    return found

def output_targets(task: dict) -> set[str]:
    """The case variables a task's outputs are reassigned into.

    A task's `data.outputs` holds two kinds of entry. One declares the task's raw
    output surface (`name`, `type: "jsonSchema"`, no `var`) and writes nowhere. The
    other is a reassign wire and carries `var` — the case variable the value lands in.
    Only the second kind has a target.

    `target` and `originalVar` are NOT targets: they hold the wire's own output id
    (`=status5` / `status5`), which is deliberately outside the case's variable
    namespace. Reading them reports every connector output as an undeclared variable.
    """
    out = set()
    for entry in task_outputs(task):
        target = entry.get("var")
        if isinstance(target, str) and target:
            out.add(target)
    return out


def output_wire_paths(task: dict) -> set[str]:
    """The `source` path each reassign wire reads from, with its `=` stripped.

    For a connector task this is the payload path, e.g. `response.status`. Casing here
    is load-bearing at runtime and invisible to `validate`.
    """
    out = set()
    for entry in task_outputs(task):
        source = entry.get("source")
        if isinstance(source, str) and source.startswith("="):
            out.add(source[1:])
    return out


def resource_keys(plan: dict) -> set[str]:
    """Every composite resource key the plan's bindings carry.

    The caseplan holds no raw resource GUIDs — a non-connector task binds through
    `<folderPath>.<name>`, and the connector binds its connection UUID.
    """
    return {
        str(b.get("resourceKey"))
        for b in bindings(plan)
        if b.get("resourceKey")
    }


def output_wire_names(task: dict) -> set[str]:
    """Wire-level names only.

    `displayName` is a human label the skill leaves free — reading it here would
    false-fail a build that labels an output `Response` while wiring `response`.
    """
    out = set()
    for entry in task_outputs(task):
        for key in ("name", "source", "sourcePath", "path"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                out.add(value)
    return out


def bindings(plan: dict) -> list[dict]:
    return plan.get("bindings") or []


def binding_defaults(plan: dict) -> set[str]:
    return {
        str(b.get("default"))
        for b in bindings(plan)
        if b.get("default") not in (None, "")
    }


# --- expressions --------------------------------------------------------------

_VARS_RE = re.compile(r"vars\.([A-Za-z_]\w*)")
_LITERAL_RE = re.compile(r"([!=])==\s*\"([^\"]*)\"")


def expressions(plan: dict) -> list[tuple[str, str]]:
    """Every `=...` expression in the plan, paired with a path describing where it is."""
    found: list[tuple[str, str]] = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
        elif isinstance(node, str) and node.startswith("="):
            found.append((path, node))

    walk(plan, "")
    return found


def vars_read(expression: str) -> set[str]:
    return set(_VARS_RE.findall(expression)) - {"$xref"}


def comparison_literals(expression: str) -> set[tuple[str, str]]:
    """The `=== "x"` / `!== "x"` comparisons in an expression, as (operator, literal)."""
    return {(op, lit) for op, lit in _LITERAL_RE.findall(expression)}


def canonical_comparison(expression: str) -> set[tuple[str, str, str]]:
    """Reduce a guard to (subject, operator, literal), ignoring how the subject is read.

    `vars.buyerDecision === "approve"` and
    `vars.$xref('Buyer review','Record buyer review decision','Action') === "approve"`
    both reduce to a comparison against `"approve"`. Pinning the semantics without
    pinning the spelling keeps a legal alternative from false-failing.
    """
    out = set()
    for match in re.finditer(
        r"vars\.(?:\$xref\([^)]*\)|[A-Za-z_]\w*)(?:\.[A-Za-z_]\w*)*\s*([!=])==\s*\"([^\"]*)\"",
        expression,
    ):
        subject = expression[match.start(): match.start(1)].strip()
        out.add((subject, match.group(1) + "==", match.group(2)))
    return out


# --- case level ---------------------------------------------------------------


def case_exits(plan: dict) -> list[dict]:
    return get_case_exit_conditions(plan) or []


def metadata(plan: dict) -> dict:
    return plan.get("metadata") or {}


def js_expressions(plan: dict) -> list[tuple[str, str]]:
    """Every `=js:` expression in the plan, as (json path, source), deepest first.

    Sink-blind like `surviving_xrefs`: a `=js:` lives in a guard, an SLA expression, a computed
    output and an activity input payload, so a scan of one sink misses the rest.
    """
    found: list[tuple[str, str]] = []

    def walk(node, path):
        if isinstance(node, str):
            if node.startswith("=js:"):
                found.append((path, node[len("=js:"):]))
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(plan, "")
    return found


def surviving_xrefs(plan: dict) -> dict:
    """Every unresolved `$xref(...)` marker in the plan, counted by marker text.

    Sink-blind on purpose. The markers appear in composite input payloads, in
    `conditionExpression`, in SLA expressions, in computed `=` outputs and in connector body
    fields, so a scan that walks only task inputs misses most of them.
    """
    import re
    from collections import Counter

    found: Counter = Counter()

    def walk(node):
        if isinstance(node, str):
            found.update(re.findall(r"\$xref\([^)]*\)", node))
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(plan)
    return dict(found)
