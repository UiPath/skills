#!/usr/bin/env python3
"""WikiPageviews: success path filters pageview range via Transform and sums
the matching views; error path returns a fixed string.

Usage: check_wiki_pageviews_flow.py {uipath_success|invalid_error}

Success path — one HTTP call returns all daily view counts in the range,
a Transform filter keeps days whose views exceed the hardcoded 500
threshold, and the flow returns the **sum** of those views as an integer.
UiPath article, 2024-01-01..2024-01-15 has exactly 6 days above 500
(historical pageviews don't change), summing to 4130:
  Jan  8 = 520
  Jan  9 = 806
  Jan 10 = 736
  Jan 11 = 747
  Jan 12 = 663
  Jan 15 = 658
  sum    = 4130

The threshold is hardcoded because `core.action.transform.filter`'s
`value` field is literal-only — it does not resolve `$vars.x`,
`{$vars.x}`, or `=js:` expressions. Plumbing a dynamic threshold through
Transform silently produces an empty filter output.

The sum (not count) is picked to defeat a spurious-pass mode where the
check's former regex fallback matched isolated digits inside HTTP
error-dump leaves (ETag hex like `W/"...e5e6b4b0d..."` contains an
isolated 6). With `assert_output_value` now strict-equality for numerics
AND a 4-digit expected value, a wrong answer cannot match by accident.

Error path — a bogus article makes the Wikimedia API return 404, which
fails the HTTP node. The flow must wire the HTTP node's `error` output
port (an implicit port created because `supportsErrorHandling: true` on
the v2 node) to an End node that returns the literal string 'Article not
found'. Without the error-port edge the flow Faults and the debug call
exits 1.
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
    # case: (article, date1, date2, expected_output_leaf)
    "uipath_success": ("UiPath", "20240101", "20240115", 4130),
    "invalid_error": ("ThisArticleDefinitelyDoesNotExist999", "20240101", "20240115", "Article not found"),
}


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"FAIL: Unknown case {case!r}; expected one of {list(CASES)}")

    # Require both node types — HTTP for the API call and a Transform
    # variant (generic/filter/map/group-by all share the `core.action.transform`
    # prefix) for the filter step.
    assert_flow_has_node_type(["core.action.http.v2", "core.action.transform"])

    article, date1, date2, expected = CASES[case]
    inputs = {"article": article, "date1": date1, "date2": date2}
    print(f"[{case}] Injecting inputs: {inputs} (expect {expected!r})")
    payload = run_debug(inputs=inputs, timeout=300)
    assert_output_value(payload, expected)
    print(f"OK: [{case}] output contains {expected!r}")


if __name__ == "__main__":
    main()
