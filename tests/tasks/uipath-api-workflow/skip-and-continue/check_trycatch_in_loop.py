#!/usr/bin/env python3
"""Assert a TryCatch sits INSIDE a loop body, not wrapped around the loop.

This is the whole point of the task (pattern 7 of control-flow-patterns.md) and it
cannot be checked by grep: `nested_control_flow` also contains both a loop and a
TryCatch, but with the TryCatch wrapped AROUND the loop, which aborts the batch on
the first bad element instead of skipping it. Only the nesting relationship
distinguishes the two, so this walks the tree and requires the TryCatch to be a
descendant of a `*#Body` node.

Lives in a file rather than inline in the YAML: a `>-` block scalar folds newlines
into spaces, which silently collapses multi-line Python into one invalid line. That
mistake passed `bash -n` (the shell was valid) and only failed at run time.
"""
import json
import re
import sys
from pathlib import Path

wf_path = next(
    (p for p in Path(".").rglob("Workflow.json") if p != Path("Workflow.json")),
    None,
)
if wf_path is None:
    sys.exit("FAIL: no Workflow.json inside a project folder")

wf = json.loads(wf_path.read_text())


def find_trycatch(node, in_body=False):
    """Yield keys of TryCatch activities, flagged by whether a loop body encloses them."""
    hits = []
    if isinstance(node, dict):
        for key, value in node.items():
            nested = in_body or bool(re.search(r"#Body$", str(key)))
            if isinstance(value, dict):
                if value.get("metadata", {}).get("activityType") == "TryCatch":
                    hits.append((key, in_body))
                hits += find_trycatch(value, nested)
            else:
                hits += find_trycatch(value, nested)
    elif isinstance(node, list):
        for item in node:
            hits += find_trycatch(item, in_body)
    return hits


found = find_trycatch(wf.get("do"))
if not found:
    sys.exit(f"FAIL: no TryCatch anywhere in {wf_path}")

inside = [k for k, in_body in found if in_body]
if not inside:
    outside = [k for k, _ in found]
    sys.exit(
        f"FAIL: TryCatch {outside} is outside the loop body. Wrapping the loop aborts "
        "the whole batch on the first bad element; pattern 7 puts the TryCatch INSIDE "
        "the body so a bad element is skipped and the batch continues."
    )

print(f"OK: TryCatch {inside} is inside a loop body (pattern 7) in {wf_path}")
