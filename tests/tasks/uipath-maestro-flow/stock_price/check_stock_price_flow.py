#!/usr/bin/env python3
"""StockPrice: http.v2 + decision/switch route success and error paths.

Runs debug twice:
  - symbol="AAPL"               -> outputs must contain a numeric price
                                   (AAPL has traded well above $10 for years).
  - symbol="NOTAREALTICKER999"  -> outputs must contain an error indicator
                                   (e.g. "error", "not found", "invalid").

Both runs must reach finalStatus="Completed" — a flow that terminates on the
error case isn't handling it gracefully.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    assert_outputs_contain,
    find_project_dir,
    run_debug,
)


def find_string_input_var(project_dir: str) -> str:
    """Return the first in/inout string variable ID from the flow file."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit(f"FAIL: No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    for v in (flow.get("variables") or {}).get("globals") or []:
        if v.get("direction") in ("in", "inout") and v.get("type") == "string":
            return v["id"]
    sys.exit("FAIL: No string input variable found in flow")


def main():
    # Must use the managed HTTP v2 node AND a branching node — this is what
    # makes the task a real integration rather than a hardcoded stub.
    assert_flow_has_node_type(["core.action.http.v2"])
    # Either decision or switch is acceptable for the success/error split.
    from _shared.flow_check import _find_project  # noqa: E402

    project_dir = _find_project("**/project.uiproj")
    types_seen: set[str] = set()
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            types_seen.update(n.get("type", "") for n in (json.load(f).get("nodes") or []))
    if "core.logic.decision" not in types_seen and "core.logic.switch" not in types_seen:
        sys.exit(
            f"FAIL: Flow needs a decision or switch node to branch on the HTTP "
            f"response. Node types seen: {sorted(types_seen)}"
        )

    symbol_id = find_string_input_var(project_dir)
    print(f"Symbol input variable: {symbol_id!r}")

    # ── Success case ──────────────────────────────────────────────────────
    print("\n[1/2] Running with valid symbol AAPL")
    payload = run_debug(inputs={symbol_id: "AAPL"}, timeout=300)
    # AAPL trades between ~$10 and ~$10000; any integer in that range in the
    # output means a real price made it through the success path.
    price = assert_output_int_in_range(payload, 10, 10000)
    print(f"OK: success path produced a price in range: {price}")

    # ── Failure case ──────────────────────────────────────────────────────
    print("\n[2/2] Running with invalid symbol NOTAREALTICKER999")
    payload = run_debug(inputs={symbol_id: "NOTAREALTICKER999"}, timeout=300)
    # Graceful error handling: flow must Complete and outputs must signal
    # the error — not swallow it or return a fake price.
    assert_outputs_contain(
        payload,
        ["error", "not found", "invalid", "fail", "unknown"],
        require_all=False,
    )
    print("OK: failure path completed with an error indicator in output")

    print("\nOK: Both success and error paths handled correctly")


if __name__ == "__main__":
    main()
