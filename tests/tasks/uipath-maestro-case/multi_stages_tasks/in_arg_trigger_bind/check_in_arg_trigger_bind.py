#!/usr/bin/env python3
"""InArgTriggerBind: In-args bind to the trigger named by their sourceTriggers.

Two triggers — manual (primary, T02) + timer (T03). Three In-args:
  caseId      sourceTriggers blank → bound to the PRIMARY (manual) trigger
  caseId2     sourceTriggers T02   → bound to the SAME PRIMARY trigger
                                     (explicit-primary must resolve identically to blank)
  approverId  sourceTriggers T03   → bound to the TIMER trigger

Asserts each In-arg's formal slot (variables.inputs) + companion
(variables.inputOutputs) elementId, and its trigger-output bridge
(data.uipath.outputs[]), land on the correct trigger node — and that neither
bridge leaks onto the other trigger. This proves sourceTriggers SELECTS the
bound trigger (blank → primary) instead of defaulting every In-arg to one
trigger. Structural-only (no debug): the binding is fully determined by
caseplan.json; running the case reveals nothing about which node hosts the
elementId.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    find_triggers,
    get_variables,
    read_caseplan,
)


def _service_type(node: dict):
    return ((node.get("data") or {}).get("uipath") or {}).get("serviceType")


def _trigger_outputs(node: dict) -> list:
    return ((node.get("data") or {}).get("uipath") or {}).get("outputs") or []


def _find_bridge(node: dict, arg: str) -> dict | None:
    # The In-arg bridge is a trigger-output entry forwarding the formal slot to
    # the companion: {name: <arg>, var: <arg>, source: "=vars.<formal-slot-id>"}.
    return next(
        (
            o
            for o in _trigger_outputs(node)
            if o.get("name") == arg and o.get("var") == arg
        ),
        None,
    )


def main():
    plan = read_caseplan()

    triggers = find_triggers(plan)
    assert_count(len(triggers), 2, "trigger node(s)")

    # Manual trigger carries no serviceType (or explicit "None"); timer carries
    # "Intsvc.TimerTrigger". See triggers/{manual,timer}/impl-json.md.
    manual = [t for t in triggers if _service_type(t) in (None, "None")]
    timer = [t for t in triggers if _service_type(t) == "Intsvc.TimerTrigger"]
    if len(manual) != 1 or len(timer) != 1:
        sts = [_service_type(t) for t in triggers]
        sys.exit(
            f"FAIL: expected exactly 1 manual (serviceType None/'None') + 1 timer "
            f"(serviceType 'Intsvc.TimerTrigger') trigger; got serviceTypes {sts}"
        )
    manual_node, timer_node = manual[0], timer[0]
    manual_id, timer_id = manual_node.get("id"), timer_node.get("id")

    # The manual trigger is the primary (T02): the SDD lists it first and it is
    # the only non-timer trigger, so a blank-sourceTriggers In-arg (caseId) must
    # bind to it. Assertions below compare against the ACTUAL minted node ids
    # (manual_id / timer_id) — NOT any literal node-id convention — so the check
    # holds however the primary trigger's id was generated. A primacy swap or a
    # wrong sourceTriggers binding is caught by the per-arg assertions below
    # (caseId → manual_id, approverId → timer_id).

    variables = get_variables(plan)
    in_vars = variables.get("inputs") or []
    io_vars = variables.get("inputOutputs") or []

    def _formal_slot(arg: str) -> dict | None:
        return next((v for v in in_vars if v.get("name") == arg), None)

    def _companion(arg: str) -> dict | None:
        # Runtime resolves =vars.<arg> by the companion's `id` (the resolver
        # matches Variable.id — see io-binding/impl-json.md). Match STRICTLY by
        # id; `name` is asserted separately below so a {name:<arg>, id:<wrong>}
        # companion (which would leave =vars.<arg> unresolvable) fails, not passes.
        return next((v for v in io_vars if v.get("id") == arg), None)

    # (arg, bound node + id, the OTHER node + id, human label)
    expectations = [
        ("approverId", timer_node, timer_id, manual_node, manual_id,
         "T03 timer (explicit sourceTriggers=T03)"),
        ("caseId", manual_node, manual_id, timer_node, timer_id,
         "primary manual trigger (blank sourceTriggers)"),
        ("caseId2", manual_node, manual_id, timer_node, timer_id,
         "primary manual trigger (explicit sourceTriggers=T02)"),
    ]

    for arg, want_node, want_id, other_node, other_id, label in expectations:
        slot = _formal_slot(arg)
        if not slot:
            names = [v.get("name") for v in in_vars]
            sys.exit(
                f"FAIL: In-arg {arg!r} missing from variables.inputs (formal slot); "
                f"got {names}"
            )
        slot_id = slot.get("id")
        if slot.get("elementId") != want_id:
            sys.exit(
                f"FAIL: In-arg {arg!r} formal slot elementId should be {want_id!r} "
                f"— the {label}; got {slot.get('elementId')!r}"
            )

        comp = _companion(arg)
        if not comp:
            entries = [(v.get("name"), v.get("id")) for v in io_vars]
            sys.exit(
                f"FAIL: In-arg {arg!r} has no inputOutputs companion with id=={arg!r} "
                f"(=vars.{arg} resolves by companion id at runtime); got {entries}"
            )
        if comp.get("name") != arg:
            sys.exit(
                f"FAIL: In-arg {arg!r} companion (id={arg!r}) has name "
                f"{comp.get('name')!r}, expected {arg!r}"
            )
        if comp.get("elementId") != want_id:
            sys.exit(
                f"FAIL: In-arg {arg!r} companion elementId should be {want_id!r} "
                f"— the {label}; got {comp.get('elementId')!r}"
            )

        bridge = _find_bridge(want_node, arg)
        if not bridge:
            outs = [(o.get("name"), o.get("var")) for o in _trigger_outputs(want_node)]
            sys.exit(
                f"FAIL: In-arg {arg!r} bridge (name={arg}, var={arg}) missing from the "
                f"{label} node's data.uipath.outputs; got {outs}"
            )
        # The bridge forwards the formal slot into the companion: its source MUST
        # read the formal slot by id (=vars.<slot id>). Without this the runtime
        # copy never happens and =vars.<arg> resolves to undefined at fire.
        want_source = f"=vars.{slot_id}"
        if bridge.get("source") != want_source:
            sys.exit(
                f"FAIL: In-arg {arg!r} bridge source should be {want_source!r} "
                f"(forwards the formal slot to the companion); got "
                f"{bridge.get('source')!r}"
            )
        if _find_bridge(other_node, arg):
            sys.exit(
                f"FAIL: In-arg {arg!r} bridge wrongly also written on the other "
                f"trigger node ({other_id!r}); each In-arg binds to exactly one trigger"
            )

    print(
        "OK: 2 triggers (manual primary + timer T03). In-arg 'approverId' "
        "(sourceTriggers=T03) bound to the timer node; 'caseId' (blank) and "
        "'caseId2' (explicit T02) both bound to the primary manual node — each "
        "with formal slot + companion elementId + trigger-output bridge "
        "(source=vars.<slot id>) on its node, and no bridge leaking to the other "
        "trigger. Explicit-primary (T02) resolves identically to blank."
    )


if __name__ == "__main__":
    main()
