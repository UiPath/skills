#!/usr/bin/env python3
"""Expense GL coding — CSV + Batch Transform check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync; `transactionsFile` is a
     job-attachment input templated into the messages.
  2. An enabled built-in `batch-transform` tool with:
       - outputColumns covering GL Account, Confidence and Review Flag, each
         with a valid name (regex ^[\\w\\s\\.,!?-]+$) and a non-empty
         per-column instruction; GL Account's instruction names the six
         account codes, Confidence's names HIGH / MEDIUM / LOW, and Review
         Flag's encodes the YES/NO rule (LOW confidence, 6999, over 5,000).
         Column instructions live in a resource whose folder name is the
         agent's choice, so they are graded here rather than by the judge.
       - webSearchGrounding disabled ("it shouldn't look anything up")
       - an output destination under `expense-coding`
  3. Analyze Files is not the row processor (no analyze-attachments tool).
  4. Output contract: outputLocation, rowsProcessed (numeric), summary.
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    _norm,
    assert_autonomous,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    assert_unique_resource_ids,
    attachment_fields,
    fail,
    find_resources,
    load,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "ExpenseCodingSol" / "ExpenseCodingAgent"
COLUMN_NAME_RE = re.compile(r"^[\w\s\.,!?-]+$")
GL_CODES = ["6100", "6200", "6300", "6400", "6500", "6999"]
COLUMNS = {
    "GL Account": ["GLAccount", "GL Code", "Account"],
    "Confidence": [],
    "Review Flag": ["ReviewFlag", "Needs Review", "Review"],
}


def is_batch_transform(d: dict) -> bool:
    return (
        d.get("$resourceType") == "tool"
        and d.get("type") == "internal"
        and (d.get("properties") or {}).get("toolType") == "batch-transform"
    )


def check_batch_transform() -> None:
    _, tool = require_resource(AGENT_DIR, is_batch_transform, "Batch Transform built-in tool")
    settings = (tool.get("properties") or {}).get("settings") or {}
    cols = settings.get("outputColumns")
    if not isinstance(cols, list) or not cols:
        fail(f"batch-transform properties.settings.outputColumns must list the new columns, got {cols!r}")
    by_name = {}
    for c in cols:
        name = (c or {}).get("name") or ""
        if not COLUMN_NAME_RE.match(name):
            fail(f"output column name {name!r} violates ^[\\w\\s\\.,!?-]+$")
        if not str((c or {}).get("description") or "").strip():
            fail(f"output column {name!r} has no per-column instruction")
        by_name[_norm(name)] = c
    found = {}
    for col, aliases in COLUMNS.items():
        hit = next((by_name[_norm(a)] for a in [col, *aliases] if _norm(a) in by_name), None)
        if hit is None:
            fail(f"outputColumns missing {col!r}; got {[c.get('name') for c in cols]}")
        found[col] = str(hit.get("description"))
    missing = [code for code in GL_CODES if code not in found["GL Account"]]
    if missing:
        fail(f"GL Account instruction must name every account code; missing {missing}")
    for level in ("HIGH", "MEDIUM", "LOW"):
        if level not in found["Confidence"].upper():
            fail(f"Confidence instruction must name {level}")
    review = found["Review Flag"]
    rule = {
        "YES/NO values": all(v in review.upper() for v in ("YES", "NO")),
        "low confidence": "LOW" in review.upper(),
        "6999 account": "6999" in review,
        "5,000 amount": bool(re.search(r"5[,.\s]?000", review)),
    }
    gaps = [k for k, ok in rule.items() if not ok]
    if gaps:
        fail(f"Review Flag instruction must encode the review rule; missing {gaps}: {review!r}")
    print("OK: outputColumns carry GL Account / Confidence / Review Flag with concrete instructions")

    web = (settings.get("webSearchGrounding") or {}).get("value")
    if web != "Disabled":
        fail(f"webSearchGrounding must be Disabled (prompt: no web lookups), got {web!r}")
    dest = (settings.get("folderPathPrefix") or {}).get("value")
    if not isinstance(dest, str) or "expense-coding" not in dest:
        fail(f"batch-transform output destination must be under 'expense-coding', got {dest!r}")
    print(f"OK: web grounding disabled, output destination {dest!r}")


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {"outputLocation": ["outputPath", "outputFile"], "rowsProcessed": ["rowCount"], "summary": []},
    )
    if f["rowsProcessed"].get("type") not in ("number", "integer"):
        fail(f"rowsProcessed must be numeric, got {f['rowsProcessed']!r}")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    if "transactionsFile" not in attachment_fields(in_schema):
        fail("transactionsFile must be a job-attachment input")
    assert_inputs_referenced(agent, ["transactionsFile"])
    check_batch_transform()
    analyze = find_resources(
        AGENT_DIR, lambda d: (d.get("properties") or {}).get("toolType") == "analyze-attachments"
    )
    if analyze:
        fail("Analyze Files is the tool the prompt says couldn't cope with the CSV — row processing belongs to Batch Transform")
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
