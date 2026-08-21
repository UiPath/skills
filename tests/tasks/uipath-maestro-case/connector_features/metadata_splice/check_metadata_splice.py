#!/usr/bin/env python3
"""ConnectorSpliceCase: the Phase 3 connector splice preserves what consumers read.

Regression guard for MST-13544. The fixture hands the agent a connector task
still in its Phase 2 shape (`data.typeId` + `data.connectionId`) plus the
captured `case spec` response at `tasks/spec-cache.<elementId>.json`. The agent
must perform only the Phase 3 splice — transcribe `caseShape` context / inputs /
outputs, substitute the binding placeholders, mint ids, re-case the schema keys,
and append the root bindings.

Every assertion below is invisible to `uip maestro case validate`, which reports
`Valid` for a hand-composed context, a dropped metadata entry, and a PascalCase
leftover alike.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    _collect_keys,
    assert_studio_web_activity_ready,
    assert_task_type_present,
    connector_context_entry,
    find_caseplan,
    read_caseplan,
    task_is_skeleton,
)

ELEMENT_ID = "Stage_Sp1Ce8-tSp1Ce001"
SPEC_CACHE = os.path.join("tasks", f"spec-cache.{ELEMENT_ID}.json")


def _spec_context_names():
    """Context entry names as the CLI emitted them, from the fixture spec cache."""
    root = os.path.dirname(find_caseplan())
    for candidate in (SPEC_CACHE, os.path.join(root, "..", "..", SPEC_CACHE)):
        if os.path.exists(candidate):
            spec = json.load(open(candidate))
            case_shape = (spec.get("Data") or {}).get("CaseShape") or {}
            return [c.get("Name") for c in case_shape.get("Context") or []]
    sys.exit(
        f"FAIL: fixture spec cache {SPEC_CACHE} not found — the task cannot be graded "
        "without the response the splice was supposed to copy"
    )


def main():
    task = assert_task_type_present("execute-connector-activity")
    data = task.get("data") or {}

    if task_is_skeleton(task):
        sys.exit("FAIL: connector task is still a skeleton — the Phase 3 splice never ran")

    # 1. Context came from the spec, not from memory: same entries, same order.
    want = _spec_context_names()
    got = [c.get("name") for c in data.get("context") or []]
    if got != want:
        sys.exit(
            f"FAIL: data.context does not match the spec cache. expected {want}, got {got} — "
            "a context assembled by hand satisfies the field-name checklist but drops the "
            "subtrees only the CLI can produce"
        )

    # 2. Studio Web can render and edit the node (the MST-13544 symptom itself).
    activity_name = assert_studio_web_activity_ready(data, "execute-connector-activity task")

    # 3. Re-casing pass ran over the whole spliced subtree.
    spliced = {k: data.get(k) for k in ("context", "inputs", "outputs")}
    leftovers = sorted(k for k in _collect_keys(spliced, set()) if k[:1].isupper())
    if leftovers:
        sys.exit(
            f"FAIL: PascalCase keys left in the spliced subtree: {leftovers} — the Step 8.a "
            "re-casing pass was skipped or incomplete; the frontend reads camelCase only"
        )

    # 4. Binding placeholders substituted, and every reference resolves.
    plan = read_caseplan()
    root_bindings = {b.get("id"): b for b in plan.get("bindings") or []}
    blob = json.dumps(data)
    if "{{" in blob:
        sys.exit("FAIL: unsubstituted {{…}} binding placeholder left in the task")
    refs = [
        (c.get("value") or "").split("=bindings.", 1)[1]
        for c in data.get("context") or []
        if isinstance(c.get("value"), str) and c["value"].startswith("=bindings.")
    ]
    if not refs:
        sys.exit("FAIL: no =bindings.<id> reference in context — the connection was not bound")
    dangling = [r for r in refs if r not in root_bindings]
    if dangling:
        sys.exit(
            f"FAIL: context references binding id(s) {dangling} with no matching entry in "
            f"caseplan.json.bindings[] (present: {sorted(root_bindings)})"
        )
    incomplete = [r for r in refs if len(root_bindings[r]) != 7]
    if incomplete:
        sys.exit(
            f"FAIL: root binding(s) {incomplete} are missing fields — all 7 are required or "
            "Studio Web fails to render the task"
        )

    conn_entry = connector_context_entry(data, "connectorKey") or {}
    print(
        f"OK: Phase 3 splice preserved the metadata Studio Web reads "
        f"(connectorKey={conn_entry.get('value')!r}, \"Select activity\"={activity_name!r}, "
        f"context={len(got)} entries matching the spec cache, "
        f"{len(refs)} binding reference(s) resolved)"
    )


if __name__ == "__main__":
    main()
