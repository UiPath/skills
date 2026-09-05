#!/usr/bin/env python3
"""SupplierOnboarding: did the SDD's lifecycle survive into caseplan.json?

Eight assertions, each one a defect a plausible build actually commits and
`uip maestro case validate` accepts:

 1. Eight stages, five primary and three secondary. A build that promotes an
    exception lane to a primary stage makes it required for case completion, so a
    normal application can never close.
 2. The oversight lane is secondary AND non-interrupting. The other two secondary
    lanes take the application over; this one runs alongside it. Marking it
    interrupting freezes every application that misses the overall target.
 3. `Application rejected` has three guarded entries from three different origins.
    Splitting them into three stages, or dropping the guards, both validate clean.
 4. `Checking the application` has a second entry from `Buyer review`. That is the
    corrections loop and the only backward edge in the case.
 5. `Application withdrawn` is entered from the stage picker, not an event.
 6. Exactly three stages expose a `wait-for-user` exit. That set IS the withdrawal
    scope: the source allows withdrawal during the three review phases and not once
    setup begins. Nothing else in the plan encodes it.
 7. Three case exits, and only `required-stages-completed` marks the case complete.
    A rejected or withdrawn application must close without completing.
 8. No stage is entered from a terminal stage. A closed application cannot move.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402


def main() -> int:
    E.sdd_facts()          # refuse to grade against a fixture the parse no longer fits
    caseplan = P.load()
    problems: list[str] = []

    by_label = P.stages_by_label(caseplan)
    ids = P.stage_ids(caseplan)
    id_to_label = {v: k for k, v in ids.items()}

    # ---- 1. stage inventory --------------------------------------------------
    missing = [lbl for lbl, _slug, _kind in E.STAGES if lbl not in by_label]
    extra = sorted(set(by_label) - {lbl for lbl, _s, _k in E.STAGES})
    if missing:
        problems.append(f"missing stage(s) {missing}")
    if extra:
        problems.append(f"unexpected stage(s) {extra} — the SDD declares exactly 8")

    for lbl, _slug, kind in E.STAGES:
        node = by_label.get(lbl)
        if node is None:
            continue
        actual = "secondary" if P.is_secondary(node) else "primary"
        if actual != kind:
            problems.append(
                f"stage {lbl!r} is {actual}, the SDD makes it {kind}"
                + (
                    " — a primary stage is required for case completion, so a normal "
                    "application would never close"
                    if kind == "secondary"
                    else ""
                )
            )

    # ---- 2. the oversight lane runs alongside, it does not take over ---------
    lane = by_label.get(E.SLA_REVIEW)
    if lane is not None:
        interrupting = [
            bool(cond.get("isInterrupting")) for cond in P.entry_conditions(lane)
        ]
        if any(interrupting):
            problems.append(
                f"{E.SLA_REVIEW!r} entry is interrupting; the SDD makes it parallel "
                "oversight so the application still runs on to its own disposition"
            )
        if not P.entry_conditions(lane):
            problems.append(f"{E.SLA_REVIEW!r} has no entry condition — it can never open")

    for lbl in E.INTERRUPTING_SECONDARY:
        node = by_label.get(lbl)
        if node is None:
            continue
        if not any(bool(c.get("isInterrupting")) for c in P.entry_conditions(node)):
            problems.append(
                f"stage {lbl!r} has no interrupting entry; it takes the application "
                "over and must interrupt"
            )

    # ---- 3. rejection reachable from three origins, each guarded ------------
    rejected = by_label.get(E.REJECTED)
    if rejected is not None:
        origins: dict[str, str] = {}
        for cond in P.entry_conditions(rejected):
            for sid in P.selected_stage_ids(cond):
                origins[id_to_label.get(sid, sid)] = P.condition_expression(cond)
        wanted = {E.BUYER, E.COMPLIANCE, E.SETUP}
        if set(origins) != wanted:
            problems.append(
                f"{E.REJECTED!r} entry origins are {sorted(origins)}; the SDD reaches it "
                f"from {sorted(wanted)} — three phases producing one disposition"
            )
        for origin, expr in origins.items():
            if not expr:
                problems.append(
                    f"{E.REJECTED!r} entry from {origin!r} carries no guard; it would fire "
                    "on every exit from that phase, rejecting approved applications"
                )

    # ---- 4. the corrections loop --------------------------------------------
    checking = by_label.get(E.CHECKING)
    if checking is not None:
        conds = P.entry_conditions(checking)
        loop = [
            c for c in conds if ids.get(E.BUYER) in P.selected_stage_ids(c)
        ]
        if not loop:
            problems.append(
                f"{E.CHECKING!r} has no entry from {E.BUYER!r} — send-back for "
                "corrections cannot return the application to the checks"
            )
        else:
            for cond in loop:
                if not P.condition_expression(cond):
                    problems.append(
                        f"{E.CHECKING!r} corrections-loop entry carries no guard; every "
                        "buyer decision would send the application back"
                    )
        if not any("case-entered" in P.rule_names(c) for c in conds):
            problems.append(
                f"{E.CHECKING!r} has no `case-entered` entry — a new application never "
                "reaches the first phase"
            )

    # ---- 5. withdrawal comes from the stage picker --------------------------
    withdrawn = by_label.get(E.WITHDRAWN)
    if withdrawn is not None:
        names = {n for c in P.entry_conditions(withdrawn) for n in P.rule_names(c)}
        if "user-selected-stage" not in names:
            problems.append(
                f"{E.WITHDRAWN!r} is not entered by `user-selected-stage` (rules: "
                f"{sorted(names)}) — no connector, app or event in the source signals a "
                "withdrawal, so a person has to pick it"
            )

    # ---- 6. withdrawal scope ------------------------------------------------
    pickers = {
        lbl
        for lbl, node in by_label.items()
        if any(P.exit_type(c) == "wait-for-user" for c in P.exit_conditions(node))
    }
    if pickers != E.WAIT_FOR_USER_STAGES:
        problems.append(
            "the stages offering the withdrawal picker are "
            f"{sorted(pickers)}; the SDD offers it in {sorted(E.WAIT_FOR_USER_STAGES)}.\n"
            f"    missing: {sorted(E.WAIT_FOR_USER_STAGES - pickers)}\n"
            f"    extra:   {sorted(pickers - E.WAIT_FOR_USER_STAGES)}\n"
            "    A `wait-for-user` exit is the only thing that exposes the lane, so this "
            "set IS the withdrawal scope."
        )

    # ---- 7. case exits ------------------------------------------------------
    exits = P.case_exits(caseplan)
    if len(exits) != len(E.CASE_EXITS):
        problems.append(
            f"{len(exits)} case exit condition(s); the SDD declares {len(E.CASE_EXITS)}"
        )
    completing = [c for c in exits if c.get("marksCaseComplete") or c.get("marksComplete")]
    if len(completing) != 1:
        problems.append(
            f"{len(completing)} case exit(s) mark the case complete; exactly one should "
            "— rejection and withdrawal close the application without completing it"
        )
    else:
        names = P.rule_names(completing[0])
        if "required-stages-completed" not in names:
            problems.append(
                "the completing case exit is keyed on "
                f"{sorted(names)}; it should be `required-stages-completed`"
            )
    for cond in exits:
        marks = bool(cond.get("marksCaseComplete") or cond.get("marksComplete"))
        for sid in P.selected_stage_ids(cond):
            origin = id_to_label.get(sid, sid)
            if origin in (E.REJECTED, E.WITHDRAWN) and marks:
                problems.append(
                    f"the case exit fed by {origin!r} marks the case complete; that "
                    "outcome is not a completion"
                )

    # ---- 8. terminal stages are terminal ------------------------------------
    for terminal in sorted(E.TERMINAL_STAGES):
        tid = ids.get(terminal)
        if tid is None:
            continue
        downstream = sorted(
            lbl
            for lbl, node in by_label.items()
            if tid in {s for c in P.entry_conditions(node) for s in P.selected_stage_ids(c)}
        )
        if downstream:
            problems.append(
                f"stage(s) {downstream} are entered from the terminal stage {terminal!r}; "
                "a closed application must not move anywhere"
            )
        for cond in P.exit_conditions(by_label[terminal]):
            if P.exit_type(cond) not in ("exit-only", ""):
                problems.append(
                    f"{terminal!r} exit {P.exit_type(cond)!r} is not `exit-only`"
                )

    # A stage selector is `selectedStageId`, singular, holding a bare string. Written as the
    # plural array the case faults on its first rules evaluation, before any task opens, and
    # `uip maestro case validate` reports Valid either way.
    plural = sorted(rid for rid, key in P.stage_selector_spellings(caseplan)
                    if key == "selectedStageIds")
    if plural:
        problems.append(
            f"{len(plural)} stage selector(s) use `selectedStageIds`: {plural}. The key is "
            f"`selectedStageId`, singular, holding a bare string; the plural array stops the "
            f"rules evaluator dead and the case faults before its first task opens"
        )

    # `$xref('Stage','Task','output')` is a build-time placeholder that has to be resolved to a
    # bare `vars.<outputReferenceId>` before the artifact ships. A survivor throws the moment the
    # runtime reads the expression holding it, and `uip maestro case validate` reports Valid.
    markers = P.surviving_xrefs(caseplan)
    if markers:
        listing = ", ".join(f"{n}x {m}" for m, n in sorted(markers.items(), key=lambda kv: -kv[1])[:4])
        problems.append(
            f"{sum(markers.values())} unresolved $xref marker(s) survive: {listing}. Each one is a "
            f"build-time placeholder; the runtime reads it as a function call and the case faults "
            f"on its first rules evaluation"
        )

    print(f"checked {P.find_caseplan()}")
    print(f"stages: {sorted(by_label)}")
    if not problems:
        print(
            "OK: lifecycle survived — 8 stages (5 primary / 3 secondary), the oversight "
            "lane parallel and non-interrupting, rejection guarded from three origins, "
            "the corrections loop back into the checks, withdrawal from the stage picker "
            f"in exactly {sorted(E.WAIT_FOR_USER_STAGES)}, 3 case exits with one "
            "completion, and three terminal stages nothing re-enters"
        )
        return 0

    print(f"\nFAIL: {len(problems)} topology finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
