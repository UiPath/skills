#!/usr/bin/env python3
"""WikiPageviews: success path filters pageview range via Transform and sums
the matching views; error path returns a fixed string.

Usage: check_wiki_pageviews_flow.py {uipath_success|invalid_error}

Success path — one HTTP call returns all daily view counts in the range,
a Transform filter keeps days whose views exceed the hardcoded 500
threshold, and the flow returns the **sum** of those views as an integer.
For UiPath, 2024-01-01..2024-01-15 the originally observed sum was 4130
(Jan 8/9/10/11/12/15 above 500). Wikimedia recomputes historical
pageviews periodically, so the criterion checks that the output is a
numeric leaf in SUCCESS_RANGE — wide enough to absorb any plausible
recompute, narrow enough to rule out trivial / spurious passes (no day
matched the filter, or the agent dumped the raw HTTP response). See
https://uipath.atlassian.net/browse/MST-9302 for the rationale.

The threshold is hardcoded because `core.action.transform.filter`'s
`value` field is literal-only — it does not resolve `$vars.x`,
`{$vars.x}`, or `=js:` expressions. Plumbing a dynamic threshold through
Transform silently produces an empty filter output.

The numeric-leaf range check (rather than `assert_output_int_in_range`'s
regex extraction) defeats a spurious-pass mode where digits embedded in
HTTP error-dump leaves (e.g., ETag hex like `W/"...e5e6b4b0d..."`) could
match the range. Same defense as `assert_output_value` for numerics.

Error path — a bogus article makes the Wikimedia API return 404, which
fails the HTTP node. The flow must wire the HTTP node's `error` output
port (an implicit port created because `supportsErrorHandling: true` on
the v2 node) to an End node that returns the literal string 'Article not
found'. Without the error-port edge the flow Faults and the debug call
exits 1.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    collect_outputs,
    run_debug,
)

# Range chosen so a correct sum (originally 4130) sits comfortably inside,
# while ruling out trivial outputs (single day at threshold ≈ 500) and
# raw-dump cases (would carry totals well above 20k or non-numeric leaves).
SUCCESS_RANGE = (1000, 20000)
ERROR_STRING = "Article not found"

CASES = {
    # case: (article, date1, date2)
    "uipath_success": ("UiPath", "20240101", "20240115"),
    "invalid_error": ("ThisArticleDefinitelyDoesNotExist999", "20240101", "20240115"),
}


def _find_numeric_leaf_in_range(payload, lo, hi):
    """Return the first numeric leaf in [lo, hi] from the flow's declared
    outputs, or None. Skips bools (which subclass int) and skips digit
    extraction from string leaves — the latter is what makes this safer
    than `assert_output_int_in_range` for HTTP-heavy flows."""
    for v in collect_outputs(payload):
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) and lo <= v <= hi:
            return v
    return None


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else ""
    if case not in CASES:
        sys.exit(f"FAIL: Unknown case {case!r}; expected one of {list(CASES)}")

    # Require both node types — HTTP for the API call and a Transform
    # variant (generic/filter/map/group-by all share the `core.action.transform`
    # prefix) for the filter step.
    assert_flow_has_node_type(["core.action.http.v2", "core.action.transform"])

    article, date1, date2 = CASES[case]
    inputs = {"article": article, "date1": date1, "date2": date2}

    if case == "uipath_success":
        lo, hi = SUCCESS_RANGE
        print(f"[{case}] Injecting inputs: {inputs} (expect numeric leaf in [{lo}, {hi}])")
        payload = run_debug(inputs=inputs, timeout=300)
        match = _find_numeric_leaf_in_range(payload, lo, hi)
        if match is None:
            sys.exit(f"FAIL: No numeric output in [{lo}, {hi}]\nOutputs: {list(collect_outputs(payload))}")
        print(f"OK: [{case}] output {match} in [{lo}, {hi}]")
    else:
        print(f"[{case}] Injecting inputs: {inputs} (expect {ERROR_STRING!r})")
        payload = run_debug(inputs=inputs, timeout=300)
        assert_output_value(payload, ERROR_STRING)
        print(f"OK: [{case}] output contains {ERROR_STRING!r}")


if __name__ == "__main__":
    main()
