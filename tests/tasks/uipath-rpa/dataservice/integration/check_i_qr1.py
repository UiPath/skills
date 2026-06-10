#!/usr/bin/env python3
"""I-QR1 — two QueryEntityRecords activities: AND-compound (4 filters) + OR-pair."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_group_filter_operator,
    assert_simple_filters_contain,
    collect_simple_filters,
    get_activities,
    load,
)

ENTITY_TYPE = "local:CodingAgentsEvalEntity"


def _classify_query(activity):
    """Return ('AND', filters) or ('OR', filters) by inspecting its filter tree."""
    filters = collect_simple_filters(activity)
    fields = [f["field"] for f in filters if f["field"]]
    # Heuristic: AND-query has 4 distinct fields; OR-query has 2 Status filters
    if fields.count("Status") == 2 and len(fields) == 2:
        return ("OR", filters)
    if {"Status", "Score", "Price", "IsActive"}.issubset(set(fields)):
        return ("AND", filters)
    return (None, filters)


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activities = get_activities(root, "QueryEntityRecords", type_arg=ENTITY_TYPE)

    if len(activities) != 2:
        print(
            f"FAIL: expected 2 QueryEntityRecords on {ENTITY_TYPE}, got {len(activities)}",
            file=sys.stderr,
        )
        sys.exit(1)

    classified = [_classify_query(a) for a in activities]
    kinds = {k for k, _ in classified}
    if kinds != {"AND", "OR"}:
        print(
            f"FAIL: expected one AND-query and one OR-query; classified as {kinds}",
            file=sys.stderr,
        )
        sys.exit(1)

    for activity, (kind, _) in zip(activities, classified):
        if kind == "AND":
            assert_group_filter_operator(activity, "AND")
            assert_simple_filters_contain(
                activity,
                [
                    ("Status", "="),
                    ("Score", ">"),
                    ("Price", "<"),
                    ("IsActive", "Equals true"),
                ],
            )
        elif kind == "OR":
            assert_group_filter_operator(activity, "OR")
            # Classification already proved there are exactly 2 Status filters;
            # just verify the (Status, =) pair exists.
            assert_simple_filters_contain(activity, [("Status", "=")])

    print(f"PASS: {xaml} — two QueryEntityRecords match I-QR1 spec")
