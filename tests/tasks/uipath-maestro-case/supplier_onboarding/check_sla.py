#!/usr/bin/env python3
"""SupplierOnboarding: did the SLA responses and their per-phase wiring survive?

Seven assertions. `uip maestro case validate` accepts every failure below.

 1. The case SLA is 120 minutes and warns at 75%. Stages warn at 70%, a figure the
    source states rather than one derived from a band; copying the stage band onto
    the case fires the overall warning six minutes early.
 2. Seven stages carry an SLA, each at its own duration. The oversight lane carries
    none.
 3. Four phase breaches start a task INSIDE the breached stage: the task holds the
    `sla-status-change` rule on its OWN entry. A stage-entry rule instead re-enters
    the stage and re-runs its other tasks. Both shapes validate.
 4. The case breach enters the oversight lane, exactly once, non-interruptively.
 5. The three wrap-up phases notify on breach and start nothing. Apologising for a
    delay and promising a new date on an application already closed is wrong.
 6. The buyer's at-risk warning reaches the Category Management group, so a stalled
    review is bumped up before the deadline rather than after it.
 7. Each phase writes its revised date into its OWN slot and its delay note reads
    that same slot. One shared slot, or a note reading a sibling's slot, makes the
    note quote a date that phase never committed to. This is the regression guard
    for a defect that shipped once already: four notes read a name the case held no
    slot for, so every one of them would have gone out with the date blank.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402


def _at_risk(escalations):
    return [e for e in escalations if P.escalation_trigger(e) == "at-risk"]


def _breach(escalations):
    return [e for e in escalations if P.escalation_trigger(e) != "at-risk"]


def main() -> int:
    E.sdd_facts()
    caseplan = P.load()
    problems: list[str] = []

    by_label = P.stages_by_label(caseplan)
    _stage_ids = P.stage_ids(caseplan)

    # ---- 1. case SLA --------------------------------------------------------
    root = P.sla_rules(caseplan)
    if not root:
        problems.append(
            "the plan root carries no slaRules — the overall 15-day target was dropped, "
            "and with it every overall-target response"
        )
    else:
        count, unit = E.CASE_SLA
        match = [
            r for r in root if r.get("count") == count and str(r.get("unit")) == unit
        ]
        if not match:
            problems.append(
                f"no root SLA of {count}{unit}; found "
                f"{[(r.get('count'), r.get('unit')) for r in root]}"
            )
        pcts = {
            P.escalation_at_risk_percent(e)
            for r in root
            for e in _at_risk(P.escalations(r))
        }
        if pcts and pcts != {E.CASE_AT_RISK_PERCENT}:
            problems.append(
                f"the case at-risk band is {sorted(p for p in pcts if p is not None)}%; the "
                f"SDD sets {E.CASE_AT_RISK_PERCENT}% for the overall target and "
                f"{E.STAGE_AT_RISK_PERCENT}% for a phase, and the two are not interchangeable"
            )
        if not pcts:
            problems.append("the case SLA has no at-risk escalation")

    # ---- 2. stage SLAs ------------------------------------------------------
    for label, (count, unit) in sorted(E.STAGE_SLA.items()):
        node = by_label.get(label)
        if node is None:
            continue
        rules = P.sla_rules(node)
        if not rules:
            problems.append(f"stage {label!r} carries no slaRules — its {count}{unit} target was dropped")
            continue
        actual = [(r.get("count"), str(r.get("unit"))) for r in rules]
        if (count, unit) not in actual:
            problems.append(
                f"stage {label!r} SLA is {actual}; the SDD gives it {count}{unit}"
            )
        pcts = {
            P.escalation_at_risk_percent(e)
            for r in rules
            for e in _at_risk(P.escalations(r))
        }
        if pcts and pcts != {E.STAGE_AT_RISK_PERCENT}:
            problems.append(
                f"stage {label!r} at-risk band is "
                f"{sorted(p for p in pcts if p is not None)}%; the SDD sets "
                f"{E.STAGE_AT_RISK_PERCENT}%"
            )

    for label in sorted(E.NO_SLA_STAGES):
        node = by_label.get(label)
        if node is not None and P.sla_rules(node):
            problems.append(
                f"stage {label!r} declares an SLA; the SDD gives it none — it is the "
                "response to a breach, not a thing that can breach"
            )

    # ---- 3. phase breach starts a task inside the breached stage -----------
    for task_name, (stage_label, _sla_title) in sorted(E.START_TASK_ON_BREACH.items()):
        node = by_label.get(stage_label)
        if node is None:
            continue
        found = [t for t in P.tasks(node) if P.task_name(t) == task_name]
        if not found:
            problems.append(
                f"task {task_name!r} is not inside {stage_label!r}; the SDD owns each "
                "phase's escalation in the phase that breached, so the phase it names is "
                "a literal rather than something a shared lane has to work out"
            )
            continue
        task = found[0]
        rules = [
            r
            for cond in P.task_entry_conditions(task)
            for r in P.sla_status_change_rules(cond)
        ]
        if not rules:
            names = {
                n for c in P.task_entry_conditions(task) for n in P.rule_names(c)
            }
            problems.append(
                f"task {task_name!r} has no `sla-status-change` entry rule (rules: "
                f"{sorted(names)}) — it never activates when the phase misses its deadline"
            )
        # The rule names the SLA by id, not the stage — so "own stage's SLA" means the
        # id has to be one this stage declares.
        own = P.sla_ids_of(node)
        listened = {
            str(rule.get("slaId"))
            for rule in rules
            if rule.get("slaId")
        }
        if not listened:
            problems.append(
                f"task {task_name!r} has an `sla-status-change` rule with no `slaId`; it "
                "does not name the SLA it listens to"
            )
        foreign = listened - own
        if foreign:
            all_slas = {
                sid: P.label(other)
                for other in P.stages(caseplan)
                for sid in P.sla_ids_of(other)
            }
            all_slas.update({sid: "root" for sid in P.sla_ids_of(caseplan)})
            problems.append(
                f"task {task_name!r} listens to SLA(s) {sorted(foreign)} — owned by "
                f"{sorted({all_slas.get(s, 'unknown') for s in foreign})}, not by "
                f"{stage_label!r}. A phase's escalation must fire on its own breach, or "
                "the note names a phase that did not run late."
            )

        # the same rule must NOT also sit on the stage's entry
        stage_rules = [
            r for cond in P.entry_conditions(node) for r in P.sla_status_change_rules(cond)
        ]
        if stage_rules:
            problems.append(
                f"stage {stage_label!r} carries an `sla-status-change` ENTRY rule; the "
                "breach response here is start-task, and a stage-entry rule re-enters the "
                "stage and re-runs its other tasks"
            )

    # ---- 4. the case breach enters the oversight lane ----------------------
    lane = by_label.get(E.SLA_REVIEW)
    if lane is not None:
        lane_rules = [
            (cond, r)
            for cond in P.entry_conditions(lane)
            for r in P.sla_status_change_rules(cond)
        ]
        if len(lane_rules) != 1:
            problems.append(
                f"{E.SLA_REVIEW!r} has {len(lane_rules)} `sla-status-change` entry rule(s); "
                "the SDD keys the lane on exactly one, against the root SLA"
            )
        # The lane opens on the CASE target, so its rule names a root SLA. Pointed at
        # a stage's SLA instead, the lane opens the first time any single phase runs
        # late, and a case still inside its overall target gets reviewed.
        root_sla_ids = {
            str(rule.get("id")) for rule in P.sla_rules(caseplan) if rule.get("id")
        }
        for cond, rule in lane_rules:
            if cond.get("isInterrupting"):
                problems.append(
                    f"{E.SLA_REVIEW!r} entry interrupts; the review runs alongside the "
                    "application, which must still reach its own disposition"
                )
            sla_id = str(rule.get("slaId") or "")
            if sla_id not in root_sla_ids:
                problems.append(
                    f"{E.SLA_REVIEW!r} opens on SLA {sla_id!r}, which is not one of the "
                    f"case's own {sorted(root_sla_ids)}; the lane must open on the "
                    f"overall target, not on a single phase running late"
                )

    # ---- 5. wrap-up phases notify and start nothing ------------------------
    escalation_task_names = set(E.START_TASK_ON_BREACH)
    for label in sorted(E.NOTIFY_ONLY_BREACH_STAGES):
        node = by_label.get(label)
        if node is None:
            continue
        for rule_set in P.sla_rules(node):
            for esc in _breach(P.escalations(rule_set)):
                action = P.escalation_action_type(esc)
                if action and action not in ("notify", "notification", ""):
                    problems.append(
                        f"stage {label!r} breach escalation acts by {action!r}; a wrap-up "
                        "phase notifies only — a delay apology promising a new expected "
                        "date is wrong for an application that is already closed"
                    )
        started = [
            P.task_name(t)
            for t in P.tasks(node)
            if any(P.sla_status_change_rules(c) for c in P.task_entry_conditions(t))
        ]
        if started:
            problems.append(
                f"stage {label!r} starts task(s) {started} on its own SLA event; the SDD "
                "routes no wrap-up breach into remediation work"
            )
        for name in escalation_task_names:
            if name in {P.task_name(t) for t in P.tasks(node)}:
                problems.append(
                    f"phase-escalation task {name!r} appears in wrap-up stage {label!r}"
                )

    # ---- 6. the buyer's at-risk warning reaches Category Management --------
    buyer = by_label.get(E.BUYER)
    if buyer is not None:
        recipients = {
            str(r.get("value") or r.get("target") or "")
            for rule_set in P.sla_rules(buyer)
            for esc in _at_risk(P.escalations(rule_set))
            for r in P.escalation_recipients(esc)
        }
        if not any(E.BUYER_AT_RISK_GROUP.lower() in r.lower() for r in recipients):
            problems.append(
                f"{E.BUYER!r} at-risk notifies {sorted(recipients)}; the SDD bumps a "
                f"stalled review up to {E.BUYER_AT_RISK_GROUP!r} before the deadline passes"
            )

    # ---- 7. each phase's revised date stays in its own phase ---------------
    names_to_task = {P.task_name(t): t for _stage, t in P.all_tasks(caseplan)}
    declared = P.variable_names(caseplan) | P.variable_ids(caseplan)

    for phase, slot in sorted(E.PHASE_REVISED_DATE.items()):
        if slot not in declared:
            problems.append(
                f"{phase!r} has no revised-date slot named {slot!r} in the plan's "
                "variables; its delay note has nowhere to read the new date from"
            )

        escalation = names_to_task.get(E.ESCALATION_OF_PHASE[phase])
        if escalation is None:
            continue
        written = P.output_targets(escalation)
        if slot not in written:
            problems.append(
                f"{phase!r}: escalation {E.ESCALATION_OF_PHASE[phase]!r} writes its new "
                f"expected date to {sorted(written)}, not to {slot!r}"
            )
        crossed = written & (set(E.PHASE_REVISED_DATE.values()) - {slot})
        if crossed:
            problems.append(
                f"{phase!r}: escalation writes into another phase's slot(s) {sorted(crossed)}"
            )

        note = names_to_task.get(E.DELAY_NOTE_OF_PHASE[phase])
        if note is None:
            problems.append(f"{phase!r} has no delay note task")
            continue
        read = set()
        for _input_name, expr in P.task_input_expressions(note):
            read |= P.vars_read(expr)
        if slot not in read:
            others = read & set(E.PHASE_REVISED_DATE.values())
            problems.append(
                f"{phase!r}: delay note {E.DELAY_NOTE_OF_PHASE[phase]!r} does not read "
                f"{slot!r}"
                + (
                    f" — it reads {sorted(others)}, which belongs to another phase, so the "
                    "supplier is told a date this phase never committed to"
                    if others
                    else " — the note would go out with the new expected date blank"
                )
            )

    print(f"checked {P.find_caseplan()}")
    print(
        f"case SLA: {[(r.get('count'), r.get('unit')) for r in root]}   "
        f"stage SLAs: {sum(1 for n in P.stages(caseplan) if P.sla_rules(n))}"
    )
    if not problems:
        print(
            f"OK: SLA responses survived — {E.CASE_SLA[0]}{E.CASE_SLA[1]} case target "
            f"warning at {E.CASE_AT_RISK_PERCENT}%, {len(E.STAGE_SLA)} stage SLAs at "
            f"{E.STAGE_AT_RISK_PERCENT}%, {len(E.START_TASK_ON_BREACH)} phase breaches "
            "starting a task on that stage's own event, one non-interrupting oversight "
            f"lane, {len(E.NOTIFY_ONLY_BREACH_STAGES)} notify-only wrap-ups, and each "
            "phase's revised date confined to its own slot"
        )
        return 0

    print(f"\nFAIL: {len(problems)} SLA finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
