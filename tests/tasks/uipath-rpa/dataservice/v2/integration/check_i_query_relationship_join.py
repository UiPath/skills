#!/usr/bin/env python3
"""v2 Integration (relationship-join query) — Owner.Title dot-notation + cross-entity."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_simple_filters_contain,
    get_activity,
    get_arg_expression,
    load,
)

FILE_ENTITY = "local:CodingAgentsEvalFileEntity"
ENTITY = "local:CodingAgentsEvalEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def first_token(expr: str | None) -> str:
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", expr or "")
    return m.group(1) if m else ""


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)

    query = get_activity(root, "QueryEntityRecords", type_arg=FILE_ENTITY)
    assert_simple_filters_contain(query, [("Owner.Title", "contains")])
    query_out = get_arg_expression(query, "OutputRecords")
    if not query_out:
        fail("QueryEntityRecords.OutputRecords is not bound")

    get = get_activity(root, "GetEntityRecordById", type_arg=ENTITY)
    record_id = get_arg_expression(get, "RecordId") or ""
    if first_token(record_id) != first_token(query_out):
        fail(
            f"GetEntityRecordById.RecordId must derive from {query_out!r}; "
            f"got {record_id!r}"
        )
    if not get_arg_expression(get, "OutputEntity"):
        fail("GetEntityRecordById.OutputEntity is not bound")

    print(
        f"PASS: {xaml} — relationship join wires {query_out} → GetEntityRecordById"
    )
