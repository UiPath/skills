#!/usr/bin/env python3
"""An external-agent task spliced from a saved spec, in the shape the Case Designer saves one."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.case_check import existing_caseplan, find_tasks_of_type  # noqa: E402

PROJECT = Path("LinearThreeStages") / "LinearThreeStages"
REVIEW_STAGE = "Stage_Qn7tBz"
CONNECTION_ID = "7a1e5c3d-0000-4000-8000-0000000000c1"
FOLDER_KEY = "7a1e5c3d-0000-4000-8000-0000000000f1"
PROMPT = "Summarize the open sales pipeline in one sentence."

failures = []


def check(ok, message):
    if not ok:
        failures.append(message)


def stage_holding(plan, task):
    return next((node.get("id") for node in plan.get("nodes", [])
                 if any(task in lane for lane in node.get("data", {}).get("tasks", []) if isinstance(lane, list))),
                None)


def main():
    plan = json.loads(Path(existing_caseplan(str(PROJECT / "caseplan.json")) or PROJECT / "caseplan.json").read_text())
    agents = find_tasks_of_type(plan, "external-agent")
    if len(agents) != 1:
        sys.exit(f"FAIL: expected one external-agent task, found {len(agents)}")
    task = agents[0]
    stage_id = stage_holding(plan, task)
    data = task.get("data", {})
    check(stage_id == REVIEW_STAGE, f"external-agent task is in {stage_id}, not the Review stage")
    check(task.get("isRequired") is False,
          f"isRequired is {task.get('isRequired')!r}; Review must not wait on the task")
    entry_rules = [rule.get("rule")
                   for condition in task.get("entryConditions") or []
                   for group in condition.get("rules") or []
                   for rule in group if isinstance(rule, dict)]
    check("current-stage-entered" in entry_rules,
          f"entry rules are {entry_rules!r}, not one that runs the task when the stage is entered")
    check(data.get("serviceType") == "Intsvc.SyncAgentExecution",
          f"data.serviceType is {data.get('serviceType')!r}, not 'Intsvc.SyncAgentExecution'")

    context = {c.get("name"): c for c in data.get("context", []) if isinstance(c, dict)}
    for name, value in (("connectorKey", "uipath-snowflake-cortex"),
                        ("objectName", "databases::schemas::agents::run"),
                        ("executionType", "sync"),
                        ("activityConfigurationVersion", "v2"),
                        ("resourceKey", CONNECTION_ID)):
        check(context.get(name, {}).get("value") == value,
              f"context[{name}] is {context.get(name, {}).get('value')!r}, not {value!r}")
    check(isinstance(context.get("metadata", {}).get("body"), dict), "context[metadata] carries no body")
    check(not any("{{" in json.dumps(c) for c in context.values()),
          "context still carries a {{...}} placeholder from the spec")

    bindings = {b.get("id"): b for b in plan.get("bindings", []) if isinstance(b, dict)}
    for name, attribute, default in (("connection", "ConnectionId", CONNECTION_ID),
                                     ("folderKey", "folderKey", FOLDER_KEY)):
        ref = str(context.get(name, {}).get("value", ""))
        binding = bindings.get(ref.removeprefix("=bindings.")) if ref.startswith("=bindings.") else None
        if binding is None:
            check(False, f"context[{name}] is not a =bindings.<id> reference to a root binding: {ref!r}")
            continue
        check(binding.get("resource") == "Connection", f"{name} binding resource is {binding.get('resource')!r}")
        check(binding.get("propertyAttribute") == attribute,
              f"{name} binding propertyAttribute is {binding.get('propertyAttribute')!r}")
        check(binding.get("resourceKey") == CONNECTION_ID,
              f"{name} binding resourceKey is {binding.get('resourceKey')!r}")
        check(binding.get("default") == default, f"{name} binding default is {binding.get('default')!r}")
    check(not any(isinstance(b, dict) and b.get("resource") == "Connection" for b in data.get("bindings") or []),
          "data.bindings copies a Connection binding onto the task")

    inputs = {i.get("name"): i for i in data.get("inputs", []) if isinstance(i, dict)}
    check(inputs.get("pathParameters", {}).get("body") == {"database": "SALES_DB", "schema": "PUBLIC", "name": "SALES_AGENT"},
          f"pathParameters body is {inputs.get('pathParameters', {}).get('body')!r}")
    check((inputs.get("body", {}).get("body") or {}).get("prompt") == PROMPT,
          f"body.prompt is {(inputs.get('body', {}).get('body') or {}).get('prompt')!r}")

    sidecar = json.loads((PROJECT / "bindings_v2.json").read_text())
    check(any(r.get("resource") == "Connection" and r.get("key") == CONNECTION_ID
              for r in sidecar.get("resources", [])),
          "bindings_v2.json has no Connection resource for the agent's connection; run `uip maestro case bindings sync`")

    if failures:
        sys.exit("FAIL: " + "; ".join(failures))
    print("OK: external-agent task spliced as the Designer saves it, bound at the root, sidecar in sync")


if __name__ == "__main__":
    main()
