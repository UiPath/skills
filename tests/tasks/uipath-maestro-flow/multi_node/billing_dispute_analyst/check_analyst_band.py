#!/usr/bin/env python3
"""Advisory: the analyst routed the valid $4,950 credit to manager review, the SOP's band.

Scored, not gating. Reads the decision `check_billing_dispute_analyst.py overcharge`
recorded; runs no debug of its own.
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
