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
                 valid JSON, name-agnostic)
                     -> parse_bpmn() locates and parses the .bpmn, no name hint
  I              locate/parse .bpmn, no name hint (Flow's prompt
                 names no project)                             -> parse_bpmn()
  T --ids        the three recipients' Slack user ids (advisory)  -> require_ids()
  T --connection the Slack task is bound to FLOW_FOLDER_CONNECTION_ID -> require_connection()

Usage:
    python3 check_multiselect.py               # locate + parse
    python3 check_multiselect.py --ids         # advisory id search
    python3 check_multiselect.py --connection  # connection pin
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import parse_bpmn  # noqa: E402
from _shared.check_slack_multiselect import require_connection, require_ids  # noqa: E402

RECIPIENT_IDS = ("U0BAW1WQT0F", "U02EBQA5AD9", "U0A1U64L5EG")
FLOW_FOLDER_CONNECTION_ID = "849e85d8-1aa9-4d52-8bbd-20041c8f05d8"


def main() -> None:
    if "--ids" in sys.argv[1:]:
        require_ids(None, RECIPIENT_IDS)
        return
    if "--connection" in sys.argv[1:]:
        require_connection(None, FLOW_FOLDER_CONNECTION_ID)
        return

    path, _root = parse_bpmn()
    print(f"OK: {path} exists and parses")


if __name__ == "__main__":
    main()
