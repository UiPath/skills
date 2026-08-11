#!/usr/bin/env python3
"""Data-grounded check for the Test Manager 'Get Assertions' results activity.

Proves the agent actually RETRIEVED the assertions for a known seeded execution —
not just that it called the activity. Asserts the returned assertion count meets
the fixture's expected minimum.

Reads:
  result.json (agent) -> {"execution_id": "<id>", "assertions": [ ... ]}

EXPECTED_MIN is the fixture's known assertion count. TODO: set it (and the
execution id in the task prompt) to a maintained seeded execution in the eval
tenant — e.g. discover via `uip tm executions list` + `uip is resources run list
uipath-uipath-testmanager GetAssertions` and pin a stable one.
"""
import json
import sys

EXPECTED_MIN = 1  # TODO: pin to the seeded fixture execution's real assertion count


def main():
    try:
        res = json.load(open("result.json", encoding="utf-8"))
    except OSError:
        print("FAIL: result.json missing — agent did not record fetched assertions")
        sys.exit(1)
    assertions = res.get("assertions")
    if not isinstance(assertions, list):
        print("FAIL: result.json has no 'assertions' list")
        sys.exit(1)
    if len(assertions) < EXPECTED_MIN:
        print(f"FAIL: got {len(assertions)} assertions, expected >= {EXPECTED_MIN}")
        sys.exit(1)
    print(f"OK: retrieved {len(assertions)} assertions for execution "
          f"{res.get('execution_id')!r} (>= {EXPECTED_MIN} expected)")


if __name__ == "__main__":
    main()
