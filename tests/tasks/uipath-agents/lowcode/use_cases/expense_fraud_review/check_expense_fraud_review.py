#!/usr/bin/env python3
"""Expense fraud review — document validation + HITL escalation check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. `receipt` is a job-attachment input, `claim` is an object, both
     templated into the messages; a file-reading built-in tool is enabled.
  3. An enabled escalation resource has an actionCenter channel bound to the
     deployed "FraudEscalation" app, with at least one recipient, a
     non-empty outcomeMapping using only "continue" / "end", and a task form
     (channel inputSchema with properties).
  4. Output contract: decision enum {approve, reject}, policyViolations and
     fraudSignals arrays, reviewedByHuman boolean, explanation.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_autonomous,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    assert_unique_resource_ids,
    attachment_fields,
    fail,
    is_file_reading_tool,
    load,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "ExpenseAuditSol" / "ExpenseAuditAgent"
APP_NAME = "FraudEscalation"


def check_inputs(in_schema: dict) -> None:
    if "receipt" not in attachment_fields(in_schema):
        fail("receipt must be a job-attachment input")
    claim = (in_schema.get("properties") or {}).get("claim")
    if not isinstance(claim, dict) or claim.get("type") != "object":
        fail(f"claim must be an object input, got {claim!r}")
    print("OK: receipt is a job-attachment and claim is an object")


def check_escalation() -> None:
    path, esc = require_resource(
        AGENT_DIR, lambda d: d.get("$resourceType") == "escalation", "escalation resource"
    )
    channels = [
        c for c in esc.get("channels") or []
        if isinstance(c, dict)
        and c.get("type") == "actionCenter"
        and (c.get("properties") or {}).get("appName") == APP_NAME
    ]
    if not channels:
        fail(f"{path.parent.name}: no actionCenter channel bound to appName {APP_NAME!r}")
    ch = channels[0]
    props = ch.get("properties") or {}
    if not props.get("resourceKey") or not props.get("folderName"):
        fail(f"channel must carry the app's resourceKey and folderName from discovery, got {props!r}")
    recipients = [r for r in ch.get("recipients") or [] if isinstance(r, dict) and r.get("value")]
    if not recipients:
        fail("escalation channel has no recipients — the task would route to nobody")
    outcomes = ch.get("outcomeMapping")
    if not isinstance(outcomes, dict) or not outcomes:
        fail(f"channel outcomeMapping must map the app's outcomes, got {outcomes!r}")
    bad = {k: v for k, v in outcomes.items() if v not in ("continue", "end")}
    if bad:
        fail(f"outcomeMapping values must be 'continue' or 'end', got {bad}")
    if not ((ch.get("inputSchema") or {}).get("properties")):
        fail("channel inputSchema has no properties — the reviewer's task form would be empty")
    print(
        f"OK: escalation bound to {APP_NAME!r} with {len(recipients)} recipient(s) "
        f"and outcomes {sorted(outcomes)}"
    )


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "decision": [],
            "policyViolations": ["violations"],
            "fraudSignals": [],
            "reviewedByHuman": ["humanReviewed"],
            "explanation": [],
        },
    )
    assert_enum(f["decision"], "decision", ["approve", "reject"])
    for name in ("policyViolations", "fraudSignals"):
        if f[name].get("type") != "array":
            fail(f"{name} must be an array, got {f[name]!r}")
    if f["reviewedByHuman"].get("type") != "boolean":
        fail(f"reviewedByHuman must be a boolean, got {f['reviewedByHuman']!r}")
    print("OK: list fields are arrays and reviewedByHuman is a boolean")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    check_inputs(in_schema)
    assert_inputs_referenced(agent, ["receipt", "claim"])
    require_resource(AGENT_DIR, is_file_reading_tool, "file-reading built-in tool")
    check_escalation()
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
