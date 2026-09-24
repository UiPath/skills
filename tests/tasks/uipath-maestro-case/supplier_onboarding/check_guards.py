#!/usr/bin/env python3
"""SupplierOnboarding: do the routing guards compare against values that can occur?

Six assertions. Every one of them can fail on a plan `uip maestro case validate`
calls Valid, and every failure is silent at build time and permanent at runtime.

 1. Guard literals come from the deployed forms' own output enums. The buyer form
    offers `approve` / `reject` / `sendback`; the compliance form offers
    `approve` / `reject`. A guard written against a human-readable label
    (`Decline`, `SendToSetup`, `Approve`) is never true, so that route is dead.
 2. Bank verification compares against `verified`, in both polarities.
 3. The buyer's approving exit and the rejecting entry carry complementary
    literals. Overlapping guards let one decision fire into two destinations.
 4. Every guard reads a subject the plan actually holds. A guard over an unknown
    variable evaluates to undefined and never routes.
 5. Every `=js:` expression in the plan parses as JavaScript. `uip maestro case
    validate` checks that the variable names exist and stops there, so an expression
    with an unbalanced paren is reported Valid and throws on its first evaluation.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402

# Literals that appear in a decision guard but are not in any deployed enum. These
# are the shapes an invented business label takes.
_DECISION_SUBJECT_RE = re.compile(
    r"(?:buyerDecision|complianceDecision|directorSignOffDecision|action\d*|Action)",
    re.I,
)


def _guard_expressions(caseplan) -> list[tuple[str, str]]:
    """Guards only: expressions that sit on a stage entry, stage exit, or task entry."""
    out: list[tuple[str, str]] = []
    for node in P.stages(caseplan):
        label = P.label(node)
        for kind, conds in (
            ("entry", P.entry_conditions(node)),
            ("exit", P.exit_conditions(node)),
        ):
            for cond in conds:
                expr = P.condition_expression(cond)
                if expr:
                    out.append((f"{label} / stage {kind} {cond.get('displayName')!r}", expr))
        for task in P.tasks(node):
            name = P.task_name(task)
            for cond in P.task_entry_conditions(task):
                expr = P.condition_expression(cond)
                if expr:
                    out.append((f"{label} / task {name!r} entry", expr))
            skip = P.task_skip_condition(task)
            if skip:
                out.append((f"{label} / task {name!r} skip", skip))
    for cond in P.case_exits(caseplan):
        expr = P.condition_expression(cond)
        if expr:
            out.append((f"case exit {cond.get('displayName')!r}", expr))
    return out


def _js_syntax_findings(caseplan) -> list[str]:
    """Reject any `=js:` expression that does not parse.

    `node` is what runs the CLI, so it is always present; parsing through it is the same engine
    the runtime uses rather than an approximation of it. A missing check here is worse than a
    wrong one, so an unusable node is reported as a finding rather than passed over.
    """
    expressions = P.js_expressions(caseplan)
    if not expressions:
        return []
    probe = (
        "const src = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "const bad = [];"
        "for (const [path, text] of src) {"
        "  try { new Function('return (' + text + ')'); }"
        "  catch (e) { bad.push([path, text.slice(0, 120), e.message]); }"
        "}"
        "process.stdout.write(JSON.stringify(bad));"
    )
    try:
        proc = subprocess.run(["node", "-e", probe], input=json.dumps(expressions),
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"could not parse the plan's {len(expressions)} `=js:` expression(s): {exc}"]
    if proc.returncode != 0:
        return [f"could not parse the plan's `=js:` expressions: {(proc.stderr or '')[:200]}"]
    return [
        f"the `=js:` expression at {path} does not parse ({message}): {text}"
        for path, text, message in json.loads(proc.stdout or "[]")
    ]


def main() -> int:
    facts = E.sdd_facts()
    caseplan = P.load()
    problems: list[str] = []

    guards = _guard_expressions(caseplan)
    if not guards:
        problems.append(
            "the plan carries no guarded conditions at all — every routing decision in "
            "this case is guarded, so this is a build that dropped them"
        )

    allowed = (
        E.BUYER_DECISION_VALUES
        | E.COMPLIANCE_DECISION_VALUES
        | {E.BANK_VERIFIED_VALUE}
    )

    # ---- 1 + 2. every decision literal is a value the form can emit ---------
    for where, expr in guards:
        for subject, operator, literal in P.canonical_comparison(expr):
            if not _DECISION_SUBJECT_RE.search(subject) and "bankVerification" not in subject:
                continue
            if literal in allowed:
                continue
            problems.append(
                f"{where}: guard compares {subject} {operator} {literal!r}, which none of "
                f"the deployed forms can emit. The buyer form offers "
                f"{sorted(E.BUYER_DECISION_VALUES)}; the compliance form offers "
                f"{sorted(E.COMPLIANCE_DECISION_VALUES)}; bank verification returns "
                f"{E.BANK_VERIFIED_VALUE!r}. This route is unreachable at runtime and "
                "`validate` cannot see it."
            )

    used = {
        literal
        for _where, expr in guards
        for _s, _op, literal in P.canonical_comparison(expr)
    }
    for literal in sorted(E.BUYER_DECISION_VALUES):
        if literal not in used:
            problems.append(
                f"no guard anywhere routes on the buyer outcome {literal!r}; the SDD gives "
                "that decision its own destination"
            )
    if E.BANK_VERIFIED_VALUE not in used:
        problems.append(
            f"no guard compares against {E.BANK_VERIFIED_VALUE!r}; bank verification is "
            "what decides whether setup can continue"
        )

    # ---- 3. the buyer decision cannot dual-fire -----------------------------
    by_label = P.stages_by_label(caseplan)
    buyer = by_label.get(E.BUYER)
    if buyer is not None:
        approving = set()
        diverting = set()
        for cond in P.exit_conditions(buyer):
            lits = {
                lit for _s, _op, lit in P.canonical_comparison(P.condition_expression(cond))
            }
            if P.marks_complete(cond):
                approving |= lits
            else:
                diverting |= lits
        if not approving:
            problems.append(
                f"{E.BUYER!r} has no completing exit carrying a guard; approval must be "
                "the only route that completes the phase"
            )
        overlap = approving & diverting
        if overlap:
            problems.append(
                f"{E.BUYER!r}: literal(s) {sorted(overlap)} appear on both the completing "
                "exit and a diverting exit — one decision would fire into two destinations"
            )
        if approving and approving != {"approve"}:
            problems.append(
                f"{E.BUYER!r} completing exit routes on {sorted(approving)}; only "
                "'approve' completes the phase"
            )

    compliance = by_label.get(E.COMPLIANCE)
    if compliance is not None:
        unguarded = [
            cond.get("displayName")
            for cond in P.exit_conditions(compliance)
            if not P.condition_expression(cond)
        ]
        if unguarded:
            problems.append(
                f"{E.COMPLIANCE!r} has unguarded exit(s) {unguarded}; the stage carries no "
                "unguarded completion, so the application never advances on its own"
            )

    # ---- 4. every guard subject resolves ------------------------------------
    known = P.variable_names(caseplan) | P.variable_ids(caseplan)
    for _stage, task in P.all_tasks(caseplan):
        for entry in P.task_outputs(task):
            for key in ("id", "name", "var", "originalVar"):
                value = entry.get(key)
                if isinstance(value, str) and value:
                    known.add(value)
    for where, expr in guards:
        for name in P.vars_read(expr):
            if name not in known:
                problems.append(
                    f"{where}: guard reads vars.{name}, which is neither a declared case "
                    "variable nor any task's output — it evaluates to undefined and never "
                    "routes"
                )

    # ---- 5. every =js: expression parses -----------------------------------
    problems.extend(_js_syntax_findings(caseplan))

    print(f"checked {P.find_caseplan()}")
    print(f"guards: {len(guards)}   distinct literals: {sorted(used)}")
    print(f"fixture literals: {sorted(facts['guard_literals'])}")
    if not problems:
        print(
            "OK: every routing guard compares against a value its deployed form can emit "
            f"({sorted(allowed)}), the buyer's approval and diversions carry complementary "
            f"literals, every guard subject resolves, and all {len(P.js_expressions(caseplan))} "
            "`=js:` expressions parse"
        )
        return 0

    print(f"\nFAIL: {len(problems)} guard finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
