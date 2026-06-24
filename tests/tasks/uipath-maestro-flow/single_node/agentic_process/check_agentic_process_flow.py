#!/usr/bin/env python3
"""RunAgenticProcess: a uipath.core.agentic-process node is present with the
two required ProcessOrchestration bindings (name + folderPath).

Structural-only check — we deliberately do NOT run ``flow debug`` here because
the test does not control which published agentic-process the agent picks
from the tenant registry, so we cannot pin a deterministic output to assert.
A debug-execution variant is tracked as follow-up work (needs a dedicated
stable test fixture on the tenant, similar to ``E2E_PROCESS_KEY``).
"""

import glob
import json
import os
import sys


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _find_flow():
    flows = glob.glob("**/RunAgenticProcess.flow", recursive=True)
    if not flows:
        _fail("No RunAgenticProcess.flow found under cwd")
    return flows[0]


def main():
    flow_path = _find_flow()
    with open(flow_path) as f:
        flow = json.load(f)

    # 1. At least one node with type prefix uipath.core.agentic-process.
    nodes = flow.get("nodes") or []
    ap_nodes = [
        n for n in nodes if str(n.get("type", "")).startswith("uipath.core.agentic-process.")
    ]
    if not ap_nodes:
        types_seen = sorted({n.get("type", "") for n in nodes})
        _fail(f"No uipath.core.agentic-process.* node found. Types: {types_seen}")

    # 2. Bindings must include 'name' and 'folderPath' entries with
    #    resource=process and resourceSubType=ProcessOrchestration.
    bindings = flow.get("bindings") or []
    by_attr = {b.get("propertyAttribute"): b for b in bindings}
    for attr in ("name", "folderPath"):
        b = by_attr.get(attr)
        if not b:
            _fail(
                f"Missing top-level bindings[] entry with propertyAttribute={attr!r}. "
                f"Bindings: {json.dumps(bindings, indent=2)[:1000]}"
            )
        if b.get("resource") != "process":
            _fail(f"binding {attr!r}: expected resource='process', got {b.get('resource')!r}")
        if b.get("resourceSubType") != "ProcessOrchestration":
            _fail(
                f"binding {attr!r}: expected resourceSubType='ProcessOrchestration', "
                f"got {b.get('resourceSubType')!r}"
            )
        if not b.get("resourceKey"):
            _fail(f"binding {attr!r}: resourceKey is empty")

    # 3. The agentic-process node has an `error` output mapping (implicit error
    #    port shared with all action nodes — see action-nodes shared doc).
    n = ap_nodes[0]
    outputs = n.get("outputs") or {}
    if "error" not in outputs:
        _fail(
            f"Agentic-process node {n.get('id')!r} missing 'error' output port. "
            f"Outputs: {list(outputs)}"
        )

    print(
        f"OK: agentic-process node {n.get('id')!r} present with "
        f"ProcessOrchestration bindings (name + folderPath)"
    )


if __name__ == "__main__":
    main()
