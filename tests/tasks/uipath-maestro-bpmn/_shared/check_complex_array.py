#!/usr/bin/env python3
"""ComplexArray (BPMN): locate/parse the process file, and the advisory
resolved-user-id check.

Ported from Flow `connector_features/complex_array.yaml`. The core "Slack
group-DM node has its users complex array populated" assertion (Flow
criterion 2) lives in the shared `_shared/check_slack_multiselect.py`, used
identically by `multiselect.yaml`; this script covers this task's other two
criteria, which are project-name-specific (Flow's task fixes the project name
"ComplexArrayTest", unlike multiselect's name-agnostic port).

Assertion map (Flow -> BPMN):
  F criterion 1  flow_contains.py --flow-name ComplexArrayTest '"nodes"'
                 '"edges"' (file exists and is valid JSON)             -> parse_bpmn("ComplexArrayTest") locates and parses the .bpmn
  I              locate/parse .bpmn with the ComplexArrayTest name hint -> parse_bpmn("ComplexArrayTest")
  F criterion 3  flow_contains.py --flow-name ComplexArrayTest
                 'U0B7Y855WGG' 'U05Q882RHFZ' (advisory, threshold 0)    -> check_ids(): same two literals searched in the located .bpmn's raw text (same weight/threshold)

Usage:
    python3 check_complex_array.py           # criterion 1: locate + parse
    python3 check_complex_array.py --ids     # criterion 3: advisory id search
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import fail, parse_bpmn  # noqa: E402

PROJECT_HINT = "ComplexArrayTest"
RECIPIENT_IDS = ("U0B7Y855WGG", "U05Q882RHFZ")


def check_parse() -> None:
    path, _root = parse_bpmn(PROJECT_HINT)
    print(f"OK: {path} exists and parses")


def check_ids() -> None:
    path, _root = parse_bpmn(PROJECT_HINT)
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    missing = [uid for uid in RECIPIENT_IDS if uid not in text]
    for uid in RECIPIENT_IDS:
        print(f"{'OK     ' if uid not in missing else 'MISSING'} {uid}")
    if missing:
        fail(f"resolved Slack user id(s) not found in {path}: {missing}")
    print(f"OK: {path} references both resolved Slack user ids")


def main() -> None:
    if "--ids" in sys.argv[1:]:
        check_ids()
    else:
        check_parse()


if __name__ == "__main__":
    main()
