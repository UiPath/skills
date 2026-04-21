#!/usr/bin/env python3
"""WikiPageviews: success path returns exact view-count diff; error path returns a fixed string.

Usage: check_wiki_pageviews_flow.py {uipath_success|invalid_error}

Expected diff for the success case is derived from the Wikimedia pageviews
API for the UiPath article — historical daily pageview counts don't change,
so the numbers are stable:
  2024-01-01 views = 239
  2024-01-15 views = 658
  658 - 239 = 419

The error case passes a bogus article title — the API returns 404 with no
items, and the flow must return the literal string 'Article not found'.
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

CASES = {
    # case: (article, date1, date2, expected_output_leaf)
    "uipath_success": ("UiPath", "20240101", "20240115", 419),
    "invalid_error": ("ThisArticleDefinitelyDoesNotExist999", "20240101", "20240115", "Article not found"),
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

    # Force the agent to actually make two HTTP calls — one per date. A
    # single call spanning /daily/{date1}/{date2} would also work in
    # principle, but we want this test to exercise a flow that explicitly
    # calls the API twice.
    assert_flow_has_node_type(["core.action.http.v2"])
    project_dir = find_project_dir()
    http_count = count_http_v2_nodes(project_dir)
    if http_count < 2:
        sys.exit(
            f"FAIL: Expected >= 2 core.action.http.v2 nodes (one per date), "
            f"got {http_count}"
        )

    article, date1, date2, expected = CASES[case]
    inputs = {"article": article, "date1": date1, "date2": date2}
    print(f"[{case}] Injecting inputs: {inputs} (expect {expected!r})")
    payload = run_debug(inputs=inputs, timeout=300)
    assert_output_value(payload, expected)
    print(f"OK: [{case}] output contains {expected!r}")


if __name__ == "__main__":
    main()
