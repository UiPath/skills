#!/usr/bin/env python3
"""Expense fraud review — document validation + HITL escalation check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. `receipt` is a job-attachment input and `claim` is declared, both
     templated into the messages; a file-reading built-in tool is enabled.
  3. An enabled escalation resource has an actionCenter channel bound to the
     solution-local "ExpenseFraudReview" Workflow Action app (appName,
     folderName=solution_folder, the app's Key as resourceKey), with at least
     one recipient, and channel schemas that mirror the app's action schema
     (its .app/schemas file) exactly: form inputs =
     inputs + inOuts, outputs = inOuts + outputs, outcomeMapping keys =
     outcomes, each mapped to "continue" / "end". Invented form fields —
     what happened when the app exposed no schema — fail here.
  4. The solution declares the app under resources/solution_folder/app/.
  5. Output contract: decision, policyViolations, fraudSignals,
     reviewedByHuman and explanation are declared (types are helper-only).
  Brownfield: the agent must be built inside the existing (fixture) project.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_existing_project,
    assert_autonomous,
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
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "ExpenseAuditSol" / "ExpenseAuditAgent"
APP_NAME = "ExpenseFraudReview"
APP_FOLDER = "solution_folder"
# Ground truth from the fixture copy of the solution-local app. For a local app
# `uip solution resources get` returns ActionSchema=null; the form lives in the
# project's .app/schemas/*.json; the app's Key is read from the solution at
# grading time (see current_app_key).
FIXTURE_SOL = Path(__file__).resolve().parent / "_fixtures" / "ExpenseAuditSol"
_SCHEMA = json.loads(next((FIXTURE_SOL / APP_NAME / ".app" / "schemas").glob("*.json")).read_text())
APP_INPUTS = {f["name"] for f in _SCHEMA["inputs"]}
APP_INOUTS = {f["name"] for f in _SCHEMA["inOuts"]} | {f["name"] for f in _SCHEMA["outputs"]}
APP_OUTCOMES = {o["name"] for o in _SCHEMA["outcomes"]}
SOLUTION_DIR = AGENT_DIR.parent


def current_app_key() -> str:
    """Key of the app's declaration as it is NOW in the solution. `uip solution
    resources refresh` re-registers a Studio Web app under a new key (and moves
    it out of app/workflow Action/), so the fixture's key goes stale; the
    channel must match whatever the solution currently declares."""
    keys = [
        r["key"]
        for p in (SOLUTION_DIR / "resources" / "solution_folder" / "app").rglob("*.json")
        for r in [json.loads(p.read_text()).get("resource") or {}]
        if r.get("name") == APP_NAME and r.get("kind") == "app"
    ]
    if len(keys) != 1:
        fail(f"expected one app declaration for {APP_NAME} under resources/solution_folder/app/, found {len(keys)}")
    return keys[0]


def check_inputs(in_schema: dict) -> None:
    if "receipt" not in attachment_fields(in_schema):
        fail("receipt must be a job-attachment input")
    if "claim" not in (in_schema.get("properties") or {}):
        fail("inputSchema must declare the claim input")
    print("OK: receipt is a job-attachment and claim is declared")


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
    app_key = current_app_key()
    if props.get("resourceKey") != app_key:
        fail(f"channel resourceKey must be the in-solution app's current Key {app_key!r} (from discovery), got {props.get('resourceKey')!r}")
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
    # The user prompt names these fields; their values / types (approve-reject,
    # lists, boolean) are lower-tier helper guidance and are not graded.
    assert_has_fields(
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


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
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
