#!/usr/bin/env python3
"""DelayDemo: structural check for the OOTB Delay node.

Generation-only — does not run `uip maestro flow debug` (a delay would block
the run for its full wait duration, and the BPMN timer fires only inside a
live engine). Verifies:

  1. Exactly one node with `type == "core.logic.delay"` is present (exact
     ==, so a different timer/logic variant fails).
  2. `inputs.timerType` is one of {"timeDuration", "timeDate"}.
  3. `inputs.timerPreset` is present and non-empty.
  4. If `timerPreset == "custom"`:
       - `timerType == "timeDuration"` requires non-empty `inputs.timerValue`.
       - `timerType == "timeDate"`     requires non-empty `inputs.timerDate`.
  5. `typeVersion` is present and non-empty (value is copied from the
     registry by the agent-under-test, so we do NOT pin a specific value).
  6. Wiring: `flow["edges"]` contains at least one edge whose `targetNodeId`
     is the delay node id (incoming) AND at least one edge whose
     `sourceNodeId` is the delay node id (outgoing).
"""

import glob
import json
import sys
from typing import NoReturn

NODE_TYPE = "core.logic.delay"
VALID_TIMER_TYPES = {"timeDuration", "timeDate"}


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/DelayDemo*.flow", recursive=True)
    if not flows:
        _fail("no DelayDemo*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_node(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(f"no node with type {NODE_TYPE!r}; types seen: {types}")
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node, found {len(matches)}")
    return matches[0]


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "typeVersion missing or empty — copy the `version` field from "
            "`uip maestro flow registry get core.logic.delay --output json`."
        )


def _check_timer_inputs(inputs: dict) -> None:
    timer_type = inputs.get("timerType")
    if timer_type not in VALID_TIMER_TYPES:
        _fail(
            f"inputs.timerType={timer_type!r}; must be one of "
            f"{sorted(VALID_TIMER_TYPES)}."
        )

    timer_preset = inputs.get("timerPreset")
    if not isinstance(timer_preset, str) or not timer_preset.strip():
        _fail("inputs.timerPreset missing or empty — required for a delay node.")

    if timer_preset == "custom":
        if timer_type == "timeDuration":
            timer_value = inputs.get("timerValue")
            if not isinstance(timer_value, str) or not timer_value.strip():
                _fail(
                    "inputs.timerPreset is 'custom' with timerType 'timeDuration' "
                    "but inputs.timerValue is missing or empty — add an ISO 8601 "
                    "duration (e.g. P1DT5H30M)."
                )
        elif timer_type == "timeDate":
            timer_date = inputs.get("timerDate")
            if not isinstance(timer_date, str) or not timer_date.strip():
                _fail(
                    "inputs.timerType is 'timeDate' but inputs.timerDate is missing "
                    "or empty — add an ISO 8601 datetime or `=js:` expression."
                )


def _check_wiring(flow: dict, node_id: str) -> None:
    edges = flow.get("edges") or []
    has_incoming = any(e.get("targetNodeId") == node_id for e in edges)
    has_outgoing = any(e.get("sourceNodeId") == node_id for e in edges)
    if not has_incoming:
        _fail(
            f"no incoming edge: flow.edges has no entry with targetNodeId={node_id!r}. "
            "The delay node must be reached from the trigger."
        )
    if not has_outgoing:
        _fail(
            f"no outgoing edge: flow.edges has no entry with sourceNodeId={node_id!r}. "
            "The delay node must continue to the End node."
        )


def main():
    flow = _read_flow()
    node = _find_node(flow)
    inputs = node.get("inputs") or {}

    _check_type_version(node)
    _check_timer_inputs(inputs)
    _check_wiring(flow, node["id"])

    print(
        f"OK: exactly one {NODE_TYPE} node present; "
        f"timerType={inputs.get('timerType')!r}, timerPreset={inputs.get('timerPreset')!r}; "
        f"typeVersion set; incoming and outgoing edges wired"
    )


if __name__ == "__main__":
    main()
