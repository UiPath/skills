#!/usr/bin/env python3
"""v2 Integration (query filter breadth) — three queries, distinct operator clusters."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_group_filter_operator,
    assert_simple_filters_contain,
    collect_simple_filters,
    get_activities,
    load,
)

ENTITY = "local:CodingAgentsEvalEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def has_pair(filters: list[dict], field: str, operator_substring: str) -> bool:
    """Loose match — operator string may vary slightly between CLI versions."""
    for f in filters:
        if f["field"] == field and f["operator"] and operator_substring in f["operator"]:
            return True
    return False


def classify(activity) -> str:
    """Identify which query (A/B/C) this is by signature fields."""
    filters = collect_simple_filters(activity)
    fields = {f["field"] for f in filters if f["field"]}
    if "Tags" in fields:
        return "A"
    if "ScheduledAt" in fields:
        return "B"
    if "Category" in fields:
        return "C"
    return "?"


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    queries = get_activities(root, "QueryEntityRecords", type_arg=ENTITY)

    if len(queries) != 3:
        fail(f"expected exactly 3 QueryEntityRecords activities, found {len(queries)}")

    by_kind: dict[str, object] = {}
    for q in queries:
        kind = classify(q)
        if kind == "?":
            fail(
                "could not classify a QueryEntityRecords activity — "
                "expected signature fields Tags / ScheduledAt / Category"
            )
        if kind in by_kind:
            fail(f"duplicate query kind {kind!r} — each query must be distinct")
        by_kind[kind] = q

    missing = {"A", "B", "C"} - by_kind.keys()
    if missing:
        fail(f"missing query kinds: {sorted(missing)}")

    # --- Query A: value + value-less + boolean + array (AND) ---
    qa = by_kind["A"]
    assert_group_filter_operator(qa, "AND")
    assert_simple_filters_contain(
        qa,
        [
            ("Status", "="),
            ("IsActive", "Equals true"),
            ("Tags", "contains"),
        ],
    )
    if not has_pair(collect_simple_filters(qa), "Notes", "empty"):
        fail("Query A missing (Notes, is empty) filter")

    # --- Query B: comparison + date range + nested AND/OR ---
    qb = by_kind["B"]
    assert_group_filter_operator(qb, "AND")
    assert_group_filter_operator(qb, "OR")
    assert_simple_filters_contain(
        qb,
        [
            ("Score", ">"),
            ("Price", "<"),
            ("ScheduledAt", ">"),
            ("Status", "="),
        ],
    )
    qb_filters = collect_simple_filters(qb)
    if not (
        has_pair(qb_filters, "EventDate", ">=")
        and has_pair(qb_filters, "EventDate", "<=")
    ):
        fail("Query B missing EventDate range (NoLessThan + NoMoreThan)")

    # --- Query C: string ops + negation + ChoiceSet + DATE equality ---
    qc = by_kind["C"]
    assert_simple_filters_contain(
        qc,
        [
            ("Title", "contains"),
            ("Title", "startswith"),
            ("Status", "endswith"),
            ("Status", "!="),
            ("Title", "not contains"),
            ("Category", "="),
            ("EventDate", "="),
        ],
    )

    print(f"PASS: {xaml} — three QueryEntityRecords cover the expected filter breadth")
