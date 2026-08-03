"""Shared assertions for the SLA-response battery (``tests/tasks/uipath-maestro-case/sla_response``).

The battery grades how an SLA requirement is *shaped* in ``caseplan.json``:

- ``notify-only``  — escalation only; no stage, no task, no entry condition.
- ``start-task``   — a follow-up task in the breached stage carries an ``sla-status-change``
  rule on **its own** ``entryConditions``, against that stage's own SLA. Never a stage-entry
  row on the breached stage: that re-enters the stage and re-runs every task whose
  ``shouldRunOnlyOnce`` is false (the default).
- ``enter-stage``  — a separate stage carries the entry.

and the two persisted status shapes, both CLI-verified on ``uip 1.198.0-preview.102``:

- **breach**  → ``slaId`` alone; an absent ``escalationId`` *is* the Breached representation.
- **at-risk** → ``slaId`` + a concrete at-risk ``escalationId`` **declared on that same SLA**
  (borrowing another SLA's escalation fails validate: "The escalation referenced by rule … no
  longer exists").

The Case Designer's ``"any"`` escalation sentinel is never authorable — released ``validate``
rejects it with that same error.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Iterator

SLA_RULE = "sla-status-change"

# The battery edits a staged solution, so the caseplan is always at this path.
CASEPLAN = "SlaResponse/SlaResponse/caseplan.json"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def read_plan(path: str = CASEPLAN) -> dict:
    """Read the battery's caseplan; falls back to a recursive search if it moved."""
    if not os.path.isfile(path):
        from _shared.case_check import find_caseplan

        path = find_caseplan()
    with open(path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------- stage lookup

def stage_nodes(plan: dict) -> list[dict]:
    return [n for n in plan.get("nodes") or [] if n.get("type") == "case-management:Stage"]


def is_secondary(node: dict) -> bool:
    return (node.get("data") or {}).get("stageType") == "secondary"


def primary_stages(plan: dict) -> list[dict]:
    return [n for n in stage_nodes(plan) if not is_secondary(n)]


def secondary_stages(plan: dict) -> list[dict]:
    return [n for n in stage_nodes(plan) if is_secondary(n)]


def stage_by_label(plan: dict, label: str) -> dict:
    for node in stage_nodes(plan):
        if (node.get("data") or {}).get("label") == label:
            return node
    labels = [(n.get("data") or {}).get("label") for n in stage_nodes(plan)]
    fail(f"stage {label!r} not found; stages present: {labels}")


def label_of(node: dict) -> str:
    return (node.get("data") or {}).get("label") or node.get("id") or "<unnamed>"


# ------------------------------------------------------------------ SLA lookup

def sla_rules_of(target: dict) -> list[dict]:
    """``metadata.slaRules`` for a plan, ``data.slaRules`` for a stage node."""
    if isinstance(target.get("nodes"), list):
        return (target.get("metadata") or {}).get("slaRules") or []
    return (target.get("data") or {}).get("slaRules") or []


def sla_owner_map(plan: dict) -> dict[str, str]:
    """``{slaId: owner}`` where owner is ``"root"`` or the owning stage's label."""
    owners: dict[str, str] = {}
    for rule in sla_rules_of(plan):
        if rule.get("id"):
            owners[rule["id"]] = "root"
    for node in stage_nodes(plan):
        for rule in sla_rules_of(node):
            if rule.get("id"):
                owners[rule["id"]] = label_of(node)
    return owners


def escalation_map(plan: dict) -> dict[str, dict]:
    """``{escalationId: {"slaId", "owner", "trigger", "displayName"}}``."""
    out: dict[str, dict] = {}

    def collect(rules: list[dict], owner: str) -> None:
        for rule in rules:
            for esc in rule.get("escalationRule") or []:
                if not esc.get("id"):
                    continue
                out[esc["id"]] = {
                    "slaId": rule.get("id"),
                    "owner": owner,
                    "trigger": (esc.get("triggerInfo") or {}).get("type"),
                    "displayName": esc.get("displayName"),
                }

    collect(sla_rules_of(plan), "root")
    for node in stage_nodes(plan):
        collect(sla_rules_of(node), label_of(node))
    return out


# --------------------------------------------------------- sla-status-change

def iter_sla_status_change(plan: dict) -> Iterator[tuple[dict, dict, dict]]:
    """Yield ``(stage_node, condition, rule)`` for every ``sla-status-change`` entry rule."""
    for node in stage_nodes(plan):
        for cond in (node.get("data") or {}).get("entryConditions") or []:
            for group in cond.get("rules") or []:
                for rule in group:
                    if rule.get("rule") == SLA_RULE:
                        yield node, cond, rule


def iter_task_sla_status_change(plan: dict) -> Iterator[tuple[dict, dict, dict, dict]]:
    """Yield ``(stage_node, task, condition, rule)`` for every task-entry ``sla-status-change``.

    This is the direct ``start-task`` shape: the follow-up task fires on the SLA event
    itself, with no stage re-entry. CLI-verified valid on uip 1.198.0-preview.102 for both
    a stage-owned SLA and the root SLA.
    """
    for node in stage_nodes(plan):
        for task in tasks_of(node):
            for cond in task.get("entryConditions") or []:
                for group in cond.get("rules") or []:
                    for rule in group:
                        if rule.get("rule") == SLA_RULE:
                            yield node, task, cond, rule


def sla_status_change_anywhere(plan: dict) -> list[dict]:
    """Every ``sla-status-change`` rule in the file, wherever it sits.

    Entry conditions are the only documented home, but a stage-exit / task-entry /
    case-exit row would still be a graph response — a notify-only assertion must see it.
    """
    found: list[dict] = []

    def walk(value) -> None:
        if isinstance(value, dict):
            if value.get("rule") == SLA_RULE:
                found.append(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(plan)
    return found


# ------------------------------------------------------------------ assertions

def assert_no_any_sentinel(plan: dict) -> None:
    blob = json.dumps(plan)
    if '"escalationId": "any"' in blob or '"escalationId":"any"' in blob:
        fail(
            'an sla-status-change rule uses the Case Designer "any" escalation sentinel; '
            "released `uip maestro case validate` rejects it "
            '("The escalation referenced by rule ... no longer exists"). '
            "A breach rule carries slaId alone."
        )


def assert_breach_shape(rule: dict, where: str) -> None:
    """Breach = ``slaId`` present, ``escalationId`` absent."""
    if not rule.get("slaId"):
        fail(f"{where}: sla-status-change rule has no slaId")
    if "escalationId" in rule:
        fail(
            f"{where}: a breach response must reference the SLA alone, but the rule carries "
            f"escalationId={rule['escalationId']!r}. An absent escalationId IS the persisted "
            "representation of Breached."
        )


def assert_at_risk_shape(plan: dict, rule: dict, where: str) -> None:
    """At-risk = ``slaId`` + a concrete at-risk escalation declared on that same SLA."""
    if not rule.get("slaId"):
        fail(f"{where}: sla-status-change rule has no slaId")
    esc_id = rule.get("escalationId")
    if not esc_id:
        fail(
            f"{where}: an at-risk response must name a concrete at-risk escalation; "
            "slaId alone is a Breached rule."
        )
    escalations = escalation_map(plan)
    if esc_id not in escalations:
        fail(f"{where}: escalationId {esc_id!r} does not resolve to any declared escalation")
    esc = escalations[esc_id]
    if esc["slaId"] != rule["slaId"]:
        fail(
            f"{where}: escalationId {esc_id!r} is declared on SLA {esc['slaId']!r}, not on the "
            f"referenced SLA {rule['slaId']!r}. validate rejects a borrowed escalation."
        )
    if esc["trigger"] != "at-risk":
        fail(
            f"{where}: escalationId {esc_id!r} has triggerInfo.type={esc['trigger']!r}; "
            "an at-risk response must reference an at-risk escalation."
        )


def assert_sla_resolves(plan: dict, rule: dict, where: str, *, owner: str | None = None) -> None:
    """The referenced ``slaId`` exists; optionally assert which target owns it."""
    owners = sla_owner_map(plan)
    sla_id = rule.get("slaId")
    if sla_id not in owners:
        fail(
            f"{where}: slaId {sla_id!r} does not resolve to any declared SLA rule "
            f"(declared: {sorted(owners)})"
        )
    if owner is not None and owners[sla_id] != owner:
        fail(
            f"{where}: slaId {sla_id!r} is owned by {owners[sla_id]!r}, expected {owner!r}"
        )


def assert_interrupting(cond: dict, expected: bool, where: str) -> None:
    actual = cond.get("isInterrupting")
    if actual is not expected:
        fail(
            f"{where}: isInterrupting is {actual!r}, expected {expected}. Interrupting follows "
            "what the response does to active work, not the SLA's scope."
        )


def assert_stage_count(plan: dict, expected: int) -> None:
    stages = stage_nodes(plan)
    if len(stages) != expected:
        fail(
            f"expected exactly {expected} stage node(s), found {len(stages)}: "
            f"{[label_of(n) for n in stages]}. An SLA response must not mint an extra lane."
        )


def escalations_of(target: dict, *, trigger: str | None = None) -> list[dict]:
    out = []
    for rule in sla_rules_of(target):
        for esc in rule.get("escalationRule") or []:
            if trigger is None or (esc.get("triggerInfo") or {}).get("type") == trigger:
                out.append(esc)
    return out


def assert_has_recipient(esc: dict, where: str) -> None:
    recipients = ((esc.get("action") or {}).get("recipients")) or []
    if not recipients:
        fail(f"{where}: escalation {esc.get('displayName')!r} notifies nobody (no recipients)")
    for r in recipients:
        if not r.get("scope"):
            fail(f"{where}: recipient {r!r} has no scope (User / UserGroup)")


def tasks_of(node: dict) -> list[dict]:
    out = []
    for group in (node.get("data") or {}).get("tasks") or []:
        out.extend(group)
    return out
