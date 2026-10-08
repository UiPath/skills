#!/usr/bin/env python3
"""Expense fraud review — document validation + HITL escalation check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. `receipt` is a job-attachment input, `claim` is an object, both
     templated into the messages; a file-reading built-in tool is enabled.
  3. An enabled escalation resource has an actionCenter channel bound to the
     deployed "ExpenseFraudReview" Workflow Action app (appName, folderName
     from discovery, resourceKey), with at least one recipient, and channel
     schemas that mirror the app's ActionSchema exactly: form inputs =
     inputs + inOuts, outputs = inOuts + outputs, outcomeMapping keys =
     outcomes, each mapped to "continue" / "end". Invented form fields —
     what happened when the app exposed no schema — fail here.
  4. The solution declares the app under resources/solution_folder/app/.
  5. Output contract: decision enum {approve, reject}, policyViolations and
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
APP_NAME = "ExpenseFraudReview"
APP_FOLDER = "Shared/uipath-agents/ExpenseFraudReviewSol"
# ActionSchema of the deployed app, from `uip solution resources get <KEY>`.
APP_INPUTS = {"EmployeeId", "ClaimSummary", "ReceiptFindings", "FraudSignals", "AgentRecommendation"}
APP_INOUTS = {"ReviewerComment"}
APP_OUTCOMES = {"approve", "reject"}


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
    if not props.get("resourceKey"):
        fail(f"channel must carry the app's resourceKey from discovery, got {props!r}")
    if props.get("folderName") != APP_FOLDER:
        fail(f"channel folderName must be the app's Folder {APP_FOLDER!r}, got {props.get('folderName')!r}")
    recipients = [r for r in ch.get("recipients") or [] if isinstance(r, dict) and r.get("value")]
    if not recipients:
        fail("escalation channel has no recipients — the task would route to nobody")
    outcomes = ch.get("outcomeMapping")
    if not isinstance(outcomes, dict) or not outcomes:
        fail(f"channel outcomeMapping must map the app's outcomes, got {outcomes!r}")
    bad = {k: v for k, v in outcomes.items() if v not in ("continue", "end")}
    if bad:
        fail(f"outcomeMapping values must be 'continue' or 'end', got {bad}")
    if set(outcomes) != APP_OUTCOMES:
        fail(f"outcomeMapping must map exactly the app's outcomes {sorted(APP_OUTCOMES)}, got {sorted(outcomes)}")
    form = set((ch.get("inputSchema") or {}).get("properties") or {})
    if form != APP_INPUTS | APP_INOUTS:
        fail(
            f"channel inputSchema must mirror the app form {sorted(APP_INPUTS | APP_INOUTS)}, got {sorted(form)} "
            "— fields must come from the app's ActionSchema, not be invented"
        )
    back = set((ch.get("outputSchema") or {}).get("properties") or {})
    if back != APP_INOUTS:
        fail(f"channel outputSchema must be the app's inOuts + outputs {sorted(APP_INOUTS)}, got {sorted(back)}")
    mapping = set(ch.get("inputSchemaDotnetTypeMapping") or {})
    if mapping != form:
        fail(f"inputSchemaDotnetTypeMapping keys {sorted(mapping)} must match the form fields {sorted(form)}")
    print(
        f"OK: escalation bound to {APP_NAME!r} with {len(recipients)} recipient(s) "
        f"and outcomes {sorted(outcomes)}"
    )


def check_app_declaration() -> None:
    app_dir = AGENT_DIR.parent / "resources" / "solution_folder" / "app"
    decls = [p for p in app_dir.rglob("*.json")] if app_dir.is_dir() else []
    if not decls:
        fail("solution has no app declaration under resources/solution_folder/app/ — solution resources were not refreshed")
    print(f"OK: solution declares the escalation app ({decls[0].relative_to(AGENT_DIR.parent)})")


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
    check_app_declaration()
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
