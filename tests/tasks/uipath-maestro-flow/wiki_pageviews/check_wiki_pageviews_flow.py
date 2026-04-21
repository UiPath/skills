#!/usr/bin/env python3
"""WikiPageviews: success path filters pageview range via Transform; error path returns a fixed string.

Usage: check_wiki_pageviews_flow.py {uipath_success|invalid_error}

Success path — one HTTP call returns all daily view counts in the range,
a Transform filter keeps days whose views exceed `min_views`, and the flow
returns the count. UiPath article, 2024-01-01..2024-01-15, min_views=500
has exactly 6 days above the threshold (historical pageviews don't change):
  Jan  8 = 520  ✓
  Jan  9 = 806  ✓
  Jan 10 = 736  ✓
  Jan 11 = 747  ✓
  Jan 12 = 663  ✓
  Jan 15 = 658  ✓

Error path — a bogus article makes the Wikimedia API return 404, which
faults the HTTP node by default. The flow must configure an HTTP response
branch (via `inputs.branches` with a `conditionExpression` matching 404)
and wire that `branch-{id}` source port to an End node that returns the
literal string 'Article not found'. Without a matching branch the flow
Faults and the debug call exits 1.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    run_debug,
)

CASES = {
    # case: (article, date1, date2, min_views, expected_output_leaf)
    "uipath_success": ("UiPath", "20240101", "20240115", 500, 6),
    "invalid_error": ("ThisArticleDefinitelyDoesNotExist999", "20240101", "20240115", 500, "Article not found"),
}


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"FAIL: Unknown case {case!r}; expected one of {list(CASES)}")

    # Require both node types — HTTP for the API call and a Transform
    # variant (generic/filter/map/group-by all share the `core.action.transform`
    # prefix) for the filter step.
    assert_flow_has_node_type(["core.action.http.v2", "core.action.transform"])

    article, date1, date2, min_views, expected = CASES[case]
    inputs = {"article": article, "date1": date1, "date2": date2, "min_views": min_views}
    print(f"[{case}] Injecting inputs: {inputs} (expect {expected!r})")
    payload = run_debug(inputs=inputs, timeout=300)
    assert_output_value(payload, expected)
    print(f"OK: [{case}] output contains {expected!r}")


if __name__ == "__main__":
    main()
