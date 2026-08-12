#!/usr/bin/env python3
"""Grade the Check 14 halt: an unresolvable wait-for-connector rule must never ship silently.

Regression guarded
------------------
Connector-event subscriptions register at CASE START. One surviving placeholder stub
anywhere makes the ENTIRE case non-startable — the case's own start event fails and
exactly one element executes — even when the stub sits on a non-required secondary
stage nothing routes to. `uip maestro case validate` reports `Valid` throughout, so
validate cannot be the gate.

Measured on uip 1.198 (2026-08-12), same case, one field changed:
    placeholder stub  -> start event Failed,    1 element,  validate Valid
    resolved connector-> start event Completed, 25 elements, validate Valid

Before the fix, the skill emitted the stub, logged it as an ordinary Open Item, and
reported the build complete. This checker fails exactly that outcome.

Pass conditions (either branch is a legitimate resolution)
---------------------------------------------------------
A. No stub survives  -> the agent resolved the connector or removed the rule.
   Additionally require structural coherence, so "removal" cannot mean gutting the
   file into something incoherent.
B. A stub survives   -> the agent MUST have halted: tasks/build-issues.md carries the
   literal BLOCKED marker line from implementation.md Step 12 Check 14.

Fail
----
A stub survives with no BLOCKED marker  -> a dead case was emitted as if complete.
That is the pre-fix behaviour and the whole point of this test.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# implementation.md § Step 12 Check 14 mandates this literal line in build-issues.md.
BLOCKED_MARKER = re.compile(
    r"BLOCKED:\s*case is not startable\s*[—-]\s*\d+\s+unresolved wait-for-connector rule\(s\)"
    r"\s+still carry the placeholder stub\.",
    re.IGNORECASE,
)

PLACEHOLDER = "placeholder"


def find_one(root: Path, name: str) -> Path | None:
    hits = [
        p
        for p in root.rglob(name)
        if ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    return hits[0] if hits else None


def context_is_stub(rule: dict) -> bool:
    """True when the rule still carries the Phase 2 placeholder context."""
    ctx = (rule.get("uipath") or {}).get("context") or []
    if not isinstance(ctx, list):
        return False
    by_name = {
        e.get("name"): e.get("value")
        for e in ctx
        if isinstance(e, dict)
    }
    return (
        by_name.get("connectorKey") == PLACEHOLDER
        or by_name.get("operation") == PLACEHOLDER
    )


def walk_conditions(case: dict):
    """Yield (scope, owner_label, condition, rule) across all four condition scopes."""
    for cond in (case.get("metadata") or {}).get("caseExitRules") or []:
        for grp in cond.get("rules") or []:
            for rule in grp:
                yield "case-exit", "root", cond, rule

    for node in case.get("nodes") or []:
        if node.get("type") != "case-management:Stage":
            continue
        data = node.get("data") or {}
        label = data.get("label") or node.get("id")
        for scope_key, scope in (
            ("entryConditions", "stage-entry"),
            ("exitConditions", "stage-exit"),
        ):
            for cond in data.get(scope_key) or []:
                for grp in cond.get("rules") or []:
                    for rule in grp:
                        yield scope, label, cond, rule
        for lane in data.get("tasks") or []:
            for task in lane:
                for cond in task.get("entryConditions") or []:
                    for grp in cond.get("rules") or []:
                        for rule in grp:
                            yield (
                                "task-entry",
                                f"{label} / {task.get('displayName')}",
                                cond,
                                rule,
                            )


def structural_problems(case: dict) -> list[str]:
    """Catch a 'removal' that left the plan incoherent."""
    problems: list[str] = []
    stage_ids = {
        n.get("id")
        for n in case.get("nodes") or []
        if n.get("type") == "case-management:Stage"
    }

    for scope, owner, cond, rule in walk_conditions(case):
        where = f"{scope} on {owner}, condition {cond.get('id')!r}"
        if not rule.get("rule"):
            problems.append(f"{where}: rule {rule.get('id')!r} has no rule type")
        target = rule.get("selectedStageId")
        if target and target not in stage_ids:
            problems.append(f"{where}: selectedStageId {target!r} points at a removed stage")

    for node in case.get("nodes") or []:
        if node.get("type") != "case-management:Stage":
            continue
        data = node.get("data") or {}
        for scope_key in ("entryConditions", "exitConditions"):
            for cond in data.get(scope_key) or []:
                groups = cond.get("rules") or []
                if not groups or not any(groups):
                    problems.append(
                        f"stage {data.get('label')!r} {scope_key}: condition "
                        f"{cond.get('id')!r} has an empty rules array"
                    )
    return problems


def main() -> int:
    root = Path.cwd()

    caseplan_path = find_one(root, "caseplan.json")
    if caseplan_path is None:
        print(
            "FAIL: no caseplan.json anywhere under the sandbox.\n"
            "  Rule 8 requires the case STRUCTURE to land even when a resource is\n"
            "  unresolved (placeholder path) — halting before Phase 2 is not the\n"
            "  expected behaviour for an unresolvable connector."
        )
        return 1

    try:
        case = json.loads(caseplan_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: caseplan.json is unreadable/unparseable: {exc}")
        return 1

    stubs = [
        (scope, owner, cond.get("displayName"), rule.get("id"))
        for scope, owner, cond, rule in walk_conditions(case)
        if rule.get("rule") == "wait-for-connector" and context_is_stub(rule)
    ]

    issues_path = find_one(root, "build-issues.md")
    issues_text = ""
    if issues_path is not None:
        try:
            issues_text = issues_path.read_text()
        except OSError:
            issues_text = ""

    print(f"caseplan: {caseplan_path.relative_to(root)}")
    print(f"surviving placeholder connector-rule stubs: {len(stubs)}")
    for scope, owner, display, rule_id in stubs:
        print(f"  - [{scope}] {owner} :: {display!r} rule={rule_id}")

    if stubs:
        if BLOCKED_MARKER.search(issues_text):
            print(
                "\nPASS (branch B): a stub survives AND the build halted with the "
                "Check 14 BLOCKED marker in build-issues.md."
            )
            return 0
        where = (
            issues_path.relative_to(root) if issues_path is not None else "build-issues.md (missing)"
        )
        print(
            f"\nFAIL: {len(stubs)} placeholder connector-rule stub(s) survived, but "
            f"{where} carries no Check 14 BLOCKED marker.\n"
            "  Expected a literal line matching:\n"
            "    BLOCKED: case is not startable — <N> unresolved wait-for-connector "
            "rule(s) still carry the placeholder stub.\n"
            "  Without the halt this case is 100% non-startable (start event fails, "
            "1 element executes)\n"
            "  while `uip maestro case validate` still reports Valid — emitted as if "
            "it were complete.\n"
            "  See implementation.md § Step 12 Check 14."
        )
        return 1

    problems = structural_problems(case)
    if problems:
        print("\nFAIL: no stub survives, but the plan was left structurally incoherent:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(
        "\nPASS (branch A): no placeholder connector-rule stub survives and the "
        "remaining conditions are coherent."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
