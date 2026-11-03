#!/usr/bin/env python3
"""Grading for the multi-document uipath-rules-extraction tasks.

The agent turns `policy/` (a base travel-expense policy, two amendments, an SOP, a
FAQ and a rate schedule) into a BusinessRules project named TravelExpenseRules,
for an as-of date of 2026-10-30. Amendment 1 (effective 2026-07-01) is in force;
Amendment 2 (effective 2027-01-01) is not. The SOP and the FAQ contain
statements that contradict the policy and must not override it.

Usage: multi_doc_check.py [full|light] <mode>. `full` is the six-document e2e (seven inputs, 24
scenarios); `light` is the smoke (base, both amendments and a FAQ; four inputs, 14 scenarios).

Modes validate, profile, outcomes, norefs and notes reuse policy_check.py (a
private copy of the module, so its globals can be pointed at this project).
`ledger` checks that review-notes.md records both amendments and which one was
not applied.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_checker():
    spec = importlib.util.spec_from_file_location("policy_check_multi", HERE / "policy_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pc = _load_checker()

FULL_SCENARIOS = [
    ("M01 domestic hotel under the amended cap", ("Hotel", "Domestic", 190, True, False, False, 10), "Approve"),
    ("M02 domestic hotel at the amended cap $225", ("Hotel", "Domestic", 225, True, False, False, 10), "Approve"),
    ("M03 domestic hotel just above the amended cap", ("Hotel", "Domestic", 226, True, False, False, 10), "Reject"),
    ("M04 SOP's $250 high-cost-city practice does not override", ("Hotel", "Domestic", 240, True, False, False, 10), "Reject"),
    ("M05 international hotel at $300", ("Hotel", "International", 300, True, False, False, 10), "Approve"),
    ("M06 international hotel above $300", ("Hotel", "International", 301, True, False, False, 10), "Reject"),
    ("M07 domestic meals at the amended cap $65", ("Meal", "Domestic", 65, True, False, False, 10), "Approve"),
    ("M08 domestic meals above the amended cap", ("Meal", "Domestic", 66, True, False, False, 10), "Reject"),
    ("M09 international meals at $90", ("Meal", "International", 90, True, False, False, 10), "Approve"),
    ("M10 international meals above $90", ("Meal", "International", 91, True, False, False, 10), "Reject"),
    ("M11 airfare $800 without pre-approval", ("Airfare", "Domestic", 800, True, False, False, 10), "Approve"),
    ("M12 airfare above $800 without pre-approval", ("Airfare", "Domestic", 801, True, False, False, 10), "Reject"),
    ("M13 airfare above $800 with written pre-approval", ("Airfare", "Domestic", 801, True, True, False, 10), "Approve"),
    ("M14 FAQ's verbal approval up to $1,000 does not override", ("Airfare", "International", 950, True, False, False, 10), "Reject"),
    ("M15 $25 expense without a receipt", ("Meal", "Domestic", 25, False, False, False, 10), "Approve"),
    ("M16 $26 expense without a receipt", ("Meal", "Domestic", 26, False, False, False, 10), "Reject"),
    ("M17 Amendment 2's $20 receipt threshold is not yet effective", ("Meal", "Domestic", 22, False, False, False, 10), "Approve"),
    ("M18 alcohol is never reimbursed", ("Meal", "Domestic", 20, True, False, True, 10), "Reject"),
    ("M19 claim on day 30", ("Hotel", "Domestic", 190, True, False, False, 30), "Approve"),
    ("M20 claim on day 31", ("Hotel", "Domestic", 190, True, False, False, 31), "Refer"),
    ("M21 Amendment 2's 45-day window is not yet effective", ("Hotel", "Domestic", 190, True, False, False, 40), "Refer"),
    ("M22 amount not stated", ("Hotel", "Domestic", None, True, False, False, 10), "Refer"),
    ("M23 receipt status not stated on a larger expense", ("Hotel", "Domestic", 190, None, False, False, 10), "Refer"),
    ("M24 trip end date not stated", ("Hotel", "Domestic", 190, True, False, False, None), "Refer"),
]

LIGHT_SCENARIOS = [
    ("L01 hotel under the amended cap", ("Hotel", 190, True, 10), "Approve"),
    ("L02 hotel at the amended cap $225", ("Hotel", 225, True, 10), "Approve"),
    ("L03 hotel just above the amended cap", ("Hotel", 226, True, 10), "Reject"),
    ("L04 FAQ's verbal approval up to $250 does not override", ("Hotel", 240, True, 10), "Reject"),
    ("L05 meals at $60", ("Meal", 60, True, 10), "Approve"),
    ("L06 meals above $60", ("Meal", 61, True, 10), "Reject"),
    ("L07 $25 expense without a receipt", ("Meal", 25, False, 10), "Approve"),
    ("L08 $26 expense without a receipt", ("Meal", 26, False, 10), "Reject"),
    ("L09 Amendment 2's $20 receipt threshold is not yet effective", ("Meal", 22, False, 10), "Approve"),
    ("L10 claim on day 30", ("Hotel", 190, True, 30), "Approve"),
    ("L11 claim on day 31", ("Hotel", 190, True, 31), "Refer"),
    ("L12 amount not stated", ("Hotel", None, True, 10), "Refer"),
    ("L13 receipt status not stated on a larger expense", ("Hotel", 190, None, 10), "Refer"),
    ("L14 trip end date not stated", ("Hotel", 190, True, None), "Refer"),
]

PROFILES = {
    "full": ({"expenseType": "string", "travelType": "string", "amount": "number", "hasReceipt": "boolean",
              "hasManagerPreApproval": "boolean", "isAlcohol": "boolean", "daysAfterTripEnd": "number"}, FULL_SCENARIOS),
    "light": ({"expenseType": "string", "amount": "number", "hasReceipt": "boolean", "daysAfterTripEnd": "number"},
              LIGHT_SCENARIOS),
}


def configure(profile: str) -> None:
    inputs, scenarios = PROFILES[profile]
    pc.PROJECT_NAME = "TravelExpenseRules"
    pc.INPUTS = inputs
    pc.OUTPUT = "outcome"
    pc.SCENARIOS = scenarios


configure("full")

LEDGER_STATES = ("not yet effective", "not yet in effect", "not in effect", "not applied", "after the as-of", "future")


def ledger_ok(text: str) -> str | None:
    """None when the notes record both amendments and say Amendment 2 was not applied, else the reason."""
    text = text.lower()
    if "amendment 1" not in text or "amendment 2" not in text:
        return "review-notes.md does not mention both amendments"
    window = 160  # the not-applied wording must sit next to a mention of Amendment 2
    for match in re.finditer("amendment 2", text):
        near = text[max(0, match.start() - window): match.end() + window]
        if any(state in near for state in LEDGER_STATES):
            return None
    return "review-notes.md does not say Amendment 2 was not applied"


def grade_ledger() -> None:
    reason = ledger_ok(pc.find_one("review-notes.md").read_text(encoding="utf-8"))
    if reason:
        pc.fail(reason)
    print("OK: review-notes.md records both amendments and that Amendment 2 was not applied")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in PROFILES:
        configure(sys.argv[1])
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    mode = args[0] if args else "outcomes"
    if mode == "validate":
        pc.rc.run_validate(pc.rc.find_project(pc.PROJECT_NAME))
        print("OK: uip rules validate passes")
    elif mode in ("profile", "outcomes", "norefs", "notes"):
        {"profile": pc.grade_profile, "outcomes": pc.grade_outcomes, "norefs": pc.grade_norefs,
         "notes": pc.grade_notes}[mode]()
    elif mode == "ledger":
        grade_ledger()
    else:
        pc.fail(f"unknown mode {mode!r}")
