#!/usr/bin/env python3
"""StockPrice: one debug run per date pair, asserting the exact cents diff.

Usage: check_stock_price_flow.py {jan3_jun30|jun30_dec29}

Expected values are derived from Yahoo Finance's historical closes for PATH:
  2023-01-03 -> 12.289999961853027
  2023-06-30 -> 16.56999969482422
  2023-12-29 -> 24.84000015258789

For each case, expected cents = round((end - start) * 100). Historical closes
don't change, so these numbers are stable.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    find_project_dir,
    run_debug,
)

# Unix timestamps (UTC midnight) for NYSE trading days used below.
JAN_3_2023 = 1672704000
JUN_30_2023 = 1688083200
DEC_29_2023 = 1703808000

CASES = {
    # case: (date1, date2, expected_cents_diff)
    "jan3_jun30": (JAN_3_2023, JUN_30_2023, 428),
    "jun30_dec29": (JUN_30_2023, DEC_29_2023, 827),
}


def count_http_v2_nodes(project_dir: str) -> int:
    n = 0
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        for node in flow.get("nodes") or []:
            if node.get("type") == "core.action.http.v2":
                n += 1
    return n


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"FAIL: Unknown case {case!r}; expected one of {list(CASES)}")

    # Force the agent to actually make two HTTP calls — a single call with
    # a wider period1/period2 range would also work in principle, but we
    # want this test to exercise a flow that explicitly calls the API twice.
    assert_flow_has_node_type(["core.action.http.v2"])
    project_dir = find_project_dir()
    http_count = count_http_v2_nodes(project_dir)
    if http_count < 2:
        sys.exit(
            f"FAIL: Expected >= 2 core.action.http.v2 nodes (one per date), "
            f"got {http_count}"
        )

    date1, date2, expected = CASES[case]
    inputs = {"symbol": "PATH", "date1": date1, "date2": date2}
    print(f"[{case}] Injecting inputs: {inputs} (expect {expected} cents)")
    payload = run_debug(inputs=inputs, timeout=300)
    assert_output_value(payload, expected)
    print(f"OK: [{case}] diff = {expected} cents")


if __name__ == "__main__":
    main()
