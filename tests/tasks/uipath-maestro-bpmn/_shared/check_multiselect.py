#!/usr/bin/env python3
"""Multiselect (BPMN): locate/parse the process file.

Ported from Flow `connector_features/multiselect.yaml` criterion 1
(`flow_contains.py '"nodes"' '"edges"'`, no `--flow-name` -- Flow's prompt
fixes no project name). The core "Slack group-DM node has exactly 3 entries
in its users multiselect" assertion (Flow criterion 2) lives in the shared
`_shared/check_slack_multiselect.py`, used identically by
`complex_array.yaml`.

Assertion map (Flow -> BPMN):
  F criterion 1  flow_contains.py '"nodes"' '"edges"' (file exists and is
                 valid JSON, name-agnostic)                    -> parse_bpmn() locates and parses the .bpmn, no name hint
  I              locate/parse .bpmn, no name hint (Flow's prompt
                 names no project)                             -> parse_bpmn()
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import parse_bpmn  # noqa: E402


def main() -> None:
    path, _root = parse_bpmn()
    print(f"OK: {path} exists and parses")


if __name__ == "__main__":
    main()
