#!/usr/bin/env python3
"""v2 Quality (TryCatch branching) — Update in Try block, Delete in Catch."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_arg_references,
    assert_simple_filters_contain,
    get_activity,
    get_arg_expression,
    load,
    parent_map,
    under,
)

ENTITY = "local:CodingAgentsEvalEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _local(el: ET.Element) -> str:
    return el.tag.split("}", 1)[1] if "}" in el.tag else el.tag


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    parents = parent_map(root)

    # --- TryCatch presence + typed Catch ---
    trycatches = [el for el in root.iter() if _local(el) == "TryCatch"]
    if not trycatches:
        fail("no TryCatch activity found")
    trycatch = trycatches[0]

    catches = [el for el in trycatch.iter() if _local(el) == "Catch"]
    if not catches:
        fail("TryCatch has no Catch entries — at least one typed Catch required")

    # --- Create (must be outside TryCatch, providing the seed variable) ---
    create = get_activity(root, "CreateEntityRecord", type_arg=ENTITY)
    if under(create, parents, "TryCatch"):
        fail("CreateEntityRecord must NOT be inside the TryCatch — it seeds createdRecord")
    created_var = get_arg_expression(create, "OutputEntity")
    if not created_var:
        fail("CreateEntityRecord.OutputEntity is not bound")

    # --- Update (must be inside TryCatch.Try) ---
    update = get_activity(root, "UpdateEntityRecord", type_arg=ENTITY)
    if not under(update, parents, "TryCatch"):
        fail("UpdateEntityRecord must be inside the TryCatch")
    # The Try block is everything inside TryCatch that is NOT under a Catch.
    if under(update, parents, "Catch"):
        fail("UpdateEntityRecord must be in the Try block, not inside a Catch")
    assert_arg_references(update, "RecordId", created_var, ".Id")

    # --- Query (must be inside TryCatch.Try, after Update) ---
    query = get_activity(root, "QueryEntityRecords", type_arg=ENTITY)
    if not under(query, parents, "TryCatch"):
        fail("QueryEntityRecords must be inside the TryCatch")
    if under(query, parents, "Catch"):
        fail("QueryEntityRecords must be in the Try block, not inside a Catch")
    assert_simple_filters_contain(query, [("Score", "=")])

    # --- Delete (must be inside a Catch block) ---
    delete = get_activity(root, "DeleteEntityRecord", type_arg=ENTITY)
    if not under(delete, parents, "Catch"):
        fail("DeleteEntityRecord must be inside a Catch block (cleanup path)")
    assert_arg_references(delete, "RecordId", created_var, ".Id")

    print(
        f"PASS: {xaml} — TryCatch branching shapes correctly; "
        f"createdRecord ({created_var}) chains into Try.Update and Catch.Delete"
    )
