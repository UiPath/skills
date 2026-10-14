#!/usr/bin/env python3
"""T6 — the SDD SLA Response Map contract: three SLA statements, three different responses."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.sla_response_map_check import check, parse_map_rows  # noqa: E402


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def rows_for(rows, response):
    return [r for r in rows if r.get("response", "").casefold() == response]


def main() -> None:
    if not os.path.isfile("sdd.md"):
        fail("sdd.md was not produced")
    text = open("sdd.md").read()

    issues = check(text)
    if issues:
        joined = "\n  - ".join(issues)
        fail(f"SLA Response Map contract violations:\n  - {joined}")

    rows, _ = parse_map_rows(text)

    # (a) Triage's SLA was only ever described as an email -> notify-only, both statuses.
    triage = [r for r in rows if "triage" in r.get("scope", "").casefold()]
    if len(triage) < 2:
        fail(
            f"expected an At-Risk and a Breached row for the Triage SLA, found {len(triage)}: "
            f"{[(r.get('status'), r.get('response')) for r in triage]}"
        )
    bad = [r for r in triage if r.get("response", "").casefold() != "notify-only"]
    if bad:
        fail(
            "the Triage SLA was only ever described as an email, so both statuses are "
            f"notify-only; got {[(r.get('status'), r.get('response')) for r in bad]}. Absent a "
            "stated response, at-risk and breached are notifications."
        )

    # (b) The Assess breach starts local work in the SAME stage, without interrupting it.
    start_task = rows_for(rows, "start-task")
    if len(start_task) != 1:
        fail(
            f"expected exactly 1 start-task row (the Senior Assessor Check inside Assess), "
            f"found {len(start_task)}: {[(r.get('scope'), r.get('target')) for r in start_task]}"
        )
    row = start_task[0]
    # Target names the follow-up TASK, not the breached stage: the rule lives on that
    # task's own entry condition. Reject a bare stage name.
    target = row.get("target", "").strip()
    if target.casefold() in {"assess", "stage: assess", ""}:
        fail(
            f"the start-task row targets {target!r} \u2014 that is the breached STAGE. A start-task "
            "response names the follow-up task (the Senior Assessor Check), because the "
            "sla-status-change rule lives on that task's own entry condition, not on Assess's "
            "stage entry."
        )
    interrupting = row.get("interrupting", "").strip().casefold()
    if interrupting not in {"", "-", "\u2014", "\u2013", "n/a", "na"}:
        fail(
            f"the start-task row has Interrupting {row.get('interrupting')!r}; a start-task "
            "response is the follow-up task's own task-entry rule, which has no interrupting "
            "cell \u2014 use `-`. (`No` would imply stage re-entry, which re-runs every task in "
            "Assess whose shouldRunOnlyOnce is false.)"
        )

    # (c) The case breach hands the case to a lane that takes over.
    enter_stage = rows_for(rows, "enter-stage")
    if len(enter_stage) != 1:
        fail(
            f"expected exactly 1 enter-stage row (the case-SLA escalation lane), found "
            f"{len(enter_stage)}: {[(r.get('scope'), r.get('target')) for r in enter_stage]}"
        )
    row = enter_stage[0]
    if row.get("interrupting", "").strip().casefold() != "yes":
        fail(
            f"the enter-stage row has Interrupting {row.get('interrupting')!r}; the lane takes over "
            "until a manager clears it, so it interrupts active work"
        )

    print(
        f"PASS: SLA Response Map closed and consistent — {len(triage)} notify-only Triage row(s), "
        "1 non-interrupting start-task in Assess, 1 interrupting enter-stage lane"
    )


if __name__ == "__main__":
    main()
