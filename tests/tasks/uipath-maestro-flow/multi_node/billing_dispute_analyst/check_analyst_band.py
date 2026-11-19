#!/usr/bin/env python3
"""Advisory: the analyst routed the valid $4,950 credit to manager review, the SOP's band.

Whether a valid credit of $4,950 goes to manager review or straight to credit turns
on the SOP's confidence rule, a judgment call that flips between runs and models, so
it is scored, not gating. Reads the decision that `check_billing_dispute_analyst.py
overcharge` recorded; it runs no debug of its own.
"""
import json
import sys

DECISION_FILE = ".grading/analyst_overcharge_decision.json"


def main():
    try:
        with open(DECISION_FILE) as f:
            decisions = json.load(f)["decisions"]
    except (OSError, ValueError, KeyError):
        sys.exit("FAIL: the overcharge run recorded no decision (it failed before deciding)")
    if "manager_review" not in decisions:
        sys.exit(f"FAIL: the $4,950 credit went to {decisions}, not manager_review (the SOP's $500-$5,000 band)")
    print("OK: the $4,950 credit routed to manager_review")


if __name__ == "__main__":
    main()
