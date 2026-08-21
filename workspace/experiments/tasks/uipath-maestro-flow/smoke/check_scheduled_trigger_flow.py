#!/usr/bin/env python3
"""ScheduledReport: structural check for the scheduled trigger (`core.trigger.scheduled`).

Validate-only — does NOT run `uip maestro flow debug` (a scheduled BPMN timer
fires only inside a live engine the test sandbox cannot provision). Asserts the
flow's start node is a scheduled trigger that *replaced* the default manual
trigger and carries a valid recurring schedule:

  1. Exactly one node with `type == "core.trigger.scheduled"` (exact ==, so a
     different trigger/timer variant fails).
  2. The manual trigger is GONE and there is exactly one trigger node:
       - zero nodes of type `core.trigger.manual`;
       - the scheduled trigger is the only `core.trigger.*` node (so it
         *replaced* the manual trigger rather than being added alongside).
  3. It is the start node: no edge targets it (a trigger has no input port, so
     `edges[]` must contain no entry whose `targetNodeId` is the trigger id).
  4. Valid schedule config on the node `inputs`:
       - `timerType == "timeCycle"`;
       - `timerPreset` present and non-empty;
       - the effective cycle expression — `timerValue` when
         `timerPreset == "custom"`, otherwise `timerPreset` — is a valid ISO
         8601 repeating interval (`R/...`), matching the registry's own
         pattern. `custom` without a non-empty `timerValue` fails.
  5. `typeVersion` present and non-empty (the agent-under-test copies the
     `version` field from the registry, so we do NOT pin a specific value —
     this node has already advanced past 1.0).
  6. The scheduled-trigger *definition* is present and correct, and the manual
     definition is gone:
       - exactly one `definitions[]` entry with
         `nodeType == "core.trigger.scheduled"`, carrying
         `model.type == "bpmn:StartEvent"` and
         `model.eventDefinition == "bpmn:TimerEventDefinition"` (this is what
         makes the BPMN timer event fire);
       - zero `definitions[]` entries with `nodeType == "core.trigger.manual"`.
"""

import glob
import json
import re
import sys
from typing import NoReturn

SCHEDULED = "core.trigger.scheduled"
MANUAL = "core.trigger.manual"
TRIGGER_PREFIX = "core.trigger."

# ISO 8601 repeating-interval pattern, copied verbatim from the
# `core.trigger.scheduled` registry definition (inputDefinition.then for
# timerValue). Accepts R/PT1H, R/P1D, R/P1W, R/PT45M, R/2026-05-14T09:00:00Z/P1W, ...
CYCLE_RE = re.compile(
    r"^R\d*\/(P(?=\d|T)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?"
    r"(\/\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})?)?)?"
    r"|\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})?)?"
    r"\/P(?=\d|T)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?)$"
)


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/ScheduledReport*.flow", recursive=True)
    if not flows:
        _fail("no ScheduledReport*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _check_single_scheduled_trigger(flow: dict) -> dict:
    nodes = flow.get("nodes", [])
    triggers = [n for n in nodes if str(n.get("type", "")).startswith(TRIGGER_PREFIX)]
    scheduled = [n for n in nodes if n.get("type") == SCHEDULED]
    manual = [n for n in nodes if n.get("type") == MANUAL]

    if manual:
        _fail(
            f"found {len(manual)} {MANUAL!r} node(s) — the scheduled trigger must "
            "REPLACE the manual trigger, not coexist with it."
        )
    if not scheduled:
        types = sorted({n.get("type") for n in nodes})
        _fail(f"no node with type {SCHEDULED!r}; node types seen: {types}")
    if len(scheduled) > 1:
        _fail(f"expected exactly one {SCHEDULED!r} node, found {len(scheduled)}")
    if len(triggers) != 1:
        trig_types = sorted(n.get("type") for n in triggers)
        _fail(
            f"expected exactly one trigger node, found {len(triggers)}: {trig_types}. "
            "A flow must have exactly one trigger."
        )
    return scheduled[0]


def _check_start_node(flow: dict, node_id: str) -> None:
    edges = flow.get("edges") or []
    incoming = [e for e in edges if e.get("targetNodeId") == node_id]
    if incoming:
        _fail(
            f"the scheduled trigger ({node_id!r}) has {len(incoming)} incoming edge(s); "
            "a trigger is the flow's start node and must have no incoming edge."
        )


def _check_schedule_config(inputs: dict) -> None:
    timer_type = inputs.get("timerType")
    if timer_type != "timeCycle":
        _fail(
            f"inputs.timerType={timer_type!r}; a scheduled trigger must use "
            '"timeCycle".'
        )

    timer_preset = inputs.get("timerPreset")
    if not isinstance(timer_preset, str) or not timer_preset.strip():
        _fail("inputs.timerPreset missing or empty — required for a scheduled trigger.")

    if timer_preset == "custom":
        cycle = inputs.get("timerValue")
        if not isinstance(cycle, str) or not cycle.strip():
            _fail(
                "inputs.timerPreset is 'custom' but inputs.timerValue is missing or "
                "empty — add an ISO 8601 repeating interval (e.g. R/PT45M)."
            )
        label = "inputs.timerValue"
    else:
        cycle = timer_preset
        label = "inputs.timerPreset"

    if not CYCLE_RE.match(cycle):
        _fail(
            f"{label}={cycle!r} is not a valid ISO 8601 repeating interval "
            "(e.g. R/PT1H, R/P1D, R/PT45M)."
        )
    # A grammatically-valid but all-zero duration (e.g. R/PT0H) is a
    # never-firing schedule. Every real recurring interval has a non-zero
    # component, so require at least one.
    if not re.search(r"[1-9]", cycle):
        _fail(
            f"{label}={cycle!r} is an all-zero, never-firing schedule — "
            "use a non-zero recurring interval such as R/PT1H."
        )


def _check_type_version(node: dict) -> None:
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "typeVersion missing or empty — copy the `version` field from "
            "`uip maestro flow registry get core.trigger.scheduled --output json`."
        )


def _check_definition(flow: dict) -> None:
    defs = flow.get("definitions") or []
    if any(d.get("nodeType") == MANUAL for d in defs):
        _fail(
            f"a {MANUAL!r} entry is still present in definitions[] — remove it when "
            "replacing the manual trigger with the scheduled trigger."
        )
    sched_defs = [d for d in defs if d.get("nodeType") == SCHEDULED]
    if len(sched_defs) != 1:
        def_types = sorted(d.get("nodeType") for d in defs)
        _fail(
            f"expected exactly one definitions[] entry with nodeType {SCHEDULED!r}, "
            f"found {len(sched_defs)}; definition nodeTypes: {def_types}. Append the "
            "object from `uip maestro flow registry get core.trigger.scheduled --output json`."
        )
    model = sched_defs[0].get("model") or {}
    if model.get("type") != "bpmn:StartEvent":
        _fail(
            f"scheduled definition model.type={model.get('type')!r}; must be "
            '"bpmn:StartEvent". Re-copy the definition from the registry.'
        )
    if model.get("eventDefinition") != "bpmn:TimerEventDefinition":
        _fail(
            f"scheduled definition model.eventDefinition={model.get('eventDefinition')!r}; "
            'must be "bpmn:TimerEventDefinition" — without it the BPMN timer never fires.'
        )


def main():
    flow = _read_flow()
    node = _check_single_scheduled_trigger(flow)
    inputs = node.get("inputs") or {}

    _check_start_node(flow, node.get("id"))
    _check_schedule_config(inputs)
    _check_type_version(node)
    _check_definition(flow)

    print(
        f"OK: start node is {SCHEDULED} (manual trigger replaced); "
        f"timerType={inputs.get('timerType')!r}, timerPreset={inputs.get('timerPreset')!r}; "
        f"typeVersion set; definition carries bpmn:StartEvent + bpmn:TimerEventDefinition"
    )


if __name__ == "__main__":
    main()
