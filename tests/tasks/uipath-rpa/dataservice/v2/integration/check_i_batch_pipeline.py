#!/usr/bin/env python3
"""v2 Integration (batch pipeline) — composition + data-flow + typing."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_activity_order,
    assert_attr,
    assert_attr_bool,
    assert_group_filter_operator,
    assert_simple_filters_contain,
    get_activities,
    get_activity,
    get_arg_expression,
    load,
)
import xml.etree.ElementTree as ET

ENTITY = "local:CodingAgentsEvalEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def first_token(expr: str) -> str:
    """Pull the leading identifier from a VB expression (the upstream var)."""
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", expr or "")
    return m.group(1) if m else ""


def local_name(el: ET.Element) -> str:
    return el.tag.split("}", 1)[1] if "}" in el.tag else el.tag


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)

    # --- Activity order in document order ---
    assert_activity_order(
        root,
        [
            "CreateMultipleEntityRecords",
            "QueryEntityRecords",
            "UpdateMultipleEntityRecords",
            "UpdateMultipleEntityRecords",
            "DeleteMultipleEntityRecords",
        ],
    )

    # --- CreateMultiple ---
    create = get_activity(root, "CreateMultipleEntityRecords", type_arg=ENTITY)
    assert_attr_bool(create, "ContinueBatchOnFailure", False)
    created_var = get_arg_expression(create, "OutputRecords")
    if not created_var:
        fail("CreateMultipleEntityRecords.OutputRecords is not bound")
    if not get_arg_expression(create, "FailedRecords"):
        fail("CreateMultipleEntityRecords.FailedRecords is not bound")

    # --- Query ---
    query = get_activity(root, "QueryEntityRecords", type_arg=ENTITY)
    assert_group_filter_operator(query, "AND")
    assert_simple_filters_contain(
        query,
        [
            ("Score", ">"),
            ("IsActive", "Equals true"),
        ],
    )
    # Sort + pagination
    assert_attr(query, "SortByField", "Score")
    assert_attr_bool(query, "SortAscending", False)
    query_out_var = get_arg_expression(query, "OutputRecords")
    if not query_out_var:
        fail("QueryEntityRecords.OutputRecords is not bound")
    if not get_arg_expression(query, "TotalRecords"):
        fail("QueryEntityRecords.TotalRecords is not bound")

    # --- UpdateMultiple (expect 2: original + retry) ---
    updates = get_activities(root, "UpdateMultipleEntityRecords", type_arg=ENTITY)
    if len(updates) < 2:
        fail(
            f"expected at least 2 UpdateMultipleEntityRecords activities "
            f"(original + retry), found {len(updates)}"
        )
    update_primary, update_retry = updates[0], updates[-1]

    assert_attr_bool(update_primary, "ContinueBatchOnFailure", False)
    primary_input = get_arg_expression(update_primary, "InputRecords") or ""
    if first_token(primary_input) != first_token(query_out_var):
        fail(
            f"primary UpdateMultipleEntityRecords.InputRecords must reference "
            f"{query_out_var!r}; got {primary_input!r}"
        )
    failed_updates_var = get_arg_expression(update_primary, "FailedRecords")
    if not failed_updates_var:
        fail("primary UpdateMultipleEntityRecords.FailedRecords is not bound")

    # Retry: InputRecords must reference the failed-updates variable
    retry_input = get_arg_expression(update_retry, "InputRecords") or ""
    if first_token(retry_input) != first_token(failed_updates_var):
        fail(
            f"retry UpdateMultipleEntityRecords.InputRecords must reference "
            f"{failed_updates_var!r}; got {retry_input!r}"
        )

    # --- DeleteMultiple ---
    delete = get_activity(root, "DeleteMultipleEntityRecords", type_arg=ENTITY)
    assert_attr_bool(delete, "ContinueBatchOnFailure", False)
    delete_input = get_arg_expression(delete, "InputRecords") or ""
    if first_token(delete_input) != first_token(query_out_var):
        fail(
            f"DeleteMultipleEntityRecords.InputRecords must derive from "
            f"{query_out_var!r}; got {delete_input!r}"
        )
    if not get_arg_expression(delete, "FailedRecords"):
        fail("DeleteMultipleEntityRecords.FailedRecords is not bound")

    # --- Typing checks via raw XAML text ---
    xaml_text = Path(xaml).read_text(encoding="utf-8")
    if "Tuple" not in xaml_text:
        fail("FailedRecords must use Tuple type for batch create/update")
    if not re.search(r"IList\s*\(\s*Of\s+Guid\s*\)|List\s*\(\s*Of\s+Guid\s*\)|Collection\s*\(\s*Of\s+Guid\s*\)", xaml_text):
        fail(
            "DeleteMultipleEntityRecords must bind Guid collections "
            "(InputRecords ICollection(Of Guid) + FailedRecords IList(Of Guid))"
        )

    # ForEach loop over FailedRecords (I56 — iteration with .Item1/.Item2).
    # Locate ForEach elements and verify at least one iterates failedUpdates.
    failed_token = first_token(failed_updates_var)
    foreach_iterating_failed = None
    for el in root.iter():
        if local_name(el) != "ForEach":
            continue
        values_expr = get_arg_expression(el, "Values") or ""
        if first_token(values_expr) == failed_token:
            foreach_iterating_failed = el
            break
    if foreach_iterating_failed is None:
        fail(
            f"expected a ForEach whose Values references {failed_updates_var!r} "
            f"(no such ForEach found — agent must iterate FailedRecords)"
        )
    # And the body of that specific ForEach must access .Item1 / .Item2
    foreach_text = ET.tostring(foreach_iterating_failed, encoding="unicode")
    if ".Item1" not in foreach_text or ".Item2" not in foreach_text:
        fail(
            "ForEach over failedUpdates must access .Item1 (error message) and "
            ".Item2.<field> (failed entity) from the Tuple"
        )

    print(
        f"PASS: {xaml} — batch pipeline composition shapes correctly; "
        f"data flow: {created_var} → {query_out_var} → updates → {failed_updates_var} → delete"
    )
