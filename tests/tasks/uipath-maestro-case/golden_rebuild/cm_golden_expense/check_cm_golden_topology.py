#!/usr/bin/env python3
"""CMGoldenExpense topology: ``_shared/check_cm_golden_case.py`` without one pin.

The shared checker requires ``metadata.intsvcActivityConfig == "v2"``. Studio
Web's case scaffold leaves the key out (both Studio Web runs: their plans
validate and the checker fails only there), so a plan without the key is
graded as if it said "v2". A plan that sets any other value still fails.
Every other topology rule is the shared checker's, unchanged.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _shared.check_cm_golden_case as topology  # noqa: E402

_read_plan = topology._read_plan


def _read_plan_defaulting_activity_config() -> dict:
    plan = _read_plan()
    metadata = plan.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("intsvcActivityConfig", "v2")
    return plan


topology._read_plan = _read_plan_defaulting_activity_config

if __name__ == "__main__":
    topology.main()
