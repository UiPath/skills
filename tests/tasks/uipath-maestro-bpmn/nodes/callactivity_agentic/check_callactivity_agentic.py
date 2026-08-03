#!/usr/bin/env python3
"""Structural check for the dedicated agentic call-activity node eval.

Grades that `Orchestrator.StartAgenticProcess` (which invokes a SEPARATE Maestro
instance) is hosted on a bpmn:callActivity, and never on a serviceTask or other
in-instance host. Uses the shared bpmn_assertions activity-type helper. The
exact-value match means the Async variant does not satisfy this check.
"""

from __future__ import annotations

import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_assertions import activity_type  # noqa: E402
from _shared.bpmn_check import (  # noqa: E402
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

TYPE = "Orchestrator.StartAgenticProcess"


def elements_ci(root, local_name: str) -> list:
    """Find BPMN elements by local name, case-insensitively — the skill's
    structural-bpmn.md documents `bpmn:CallActivity`/`bpmn:SubProcess` in
    PascalCase while the spec/fixtures use camelCase, so accept both."""
    target = local_name.lower()
    return [el for el in root.iter() if el.tag.rsplit("}", 1)[-1].lower() == target]


def main() -> None:
    path, root = parse_bpmn("CallActivityAgenticBpmn")

    hosts = [c for c in elements_ci(root, "callActivity") if activity_type(c) == TYPE]
    if not hosts:
        fail(f"missing bpmn:callActivity with {TYPE}")

    # Wrong-host guard: a separate-instance invocation must not be modeled as an
    # in-instance serviceTask / task / etc.
    for kind in (
        "serviceTask",
        "sendTask",
        "task",
        "userTask",
        "businessRuleTask",
        "receiveTask",
        "scriptTask",
    ):
        offenders = [e for e in elements_ci(root, kind) if activity_type(e) == TYPE]
        if offenders:
            fail(f"{TYPE} must be on bpmn:callActivity (separate instance), found on bpmn:{kind}")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} hosts {TYPE} on a bpmn:callActivity")


if __name__ == "__main__":
    main()
