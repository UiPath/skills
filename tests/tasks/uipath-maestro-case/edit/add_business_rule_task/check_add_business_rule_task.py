#!/usr/bin/env python3
"""A v3 business-rule task bound by name + folderPath, storing one decision column in a case variable."""

import json
import sys
from pathlib import Path

PROJECT = Path("LinearThreeStages") / "LinearThreeStages"
REVIEW_STAGE = "Stage_Qn7tBz"
RULE_NAME = "CreditRisk"
RULE_FOLDER = "Shared"
RESOURCE_KEY = f"{RULE_FOLDER}.{RULE_NAME}"

failures = []


def check(ok, message):
    if not ok:
        failures.append(message)


def main():
    plan = json.loads((PROJECT / "caseplan.json").read_text())
    tasks = [
        (node["id"], task)
        for node in plan.get("nodes", [])
        for lane in node.get("data", {}).get("tasks", [])
        for task in lane
        if task.get("type") == "business-rule"
    ]
    if len(tasks) != 1:
        sys.exit(f"FAIL: expected one business-rule task, found {len(tasks)}")
    stage_id, task = tasks[0]
    data = task.get("data", {})
    check(stage_id == REVIEW_STAGE, f"business-rule task is in {stage_id}, not the Review stage")
    check("context" not in data, "task carries data.context")

    bindings = {b.get("id"): b for b in plan.get("bindings", [])}
    for field, default in (("name", RULE_NAME), ("folderPath", RULE_FOLDER)):
        ref = str(data.get(field, ""))
        binding = bindings.get(ref.removeprefix("=bindings.")) if ref.startswith("=bindings.") else None
        if binding is None:
            check(False, f"data.{field} is not a =bindings.<id> reference to a declared binding: {ref!r}")
            continue
        check(binding.get("resource") == "BusinessRule", f"{field} binding resource is {binding.get('resource')!r}")
        check(binding.get("propertyAttribute") == field, f"{field} binding propertyAttribute is {binding.get('propertyAttribute')!r}")
        check(binding.get("resourceKey") == RESOURCE_KEY, f"{field} binding resourceKey is {binding.get('resourceKey')!r}")
        check(binding.get("default") == default, f"{field} binding default is {binding.get('default')!r}")
    check(
        not any(b.get("resource") == "BusinessRule" and b.get("propertyAttribute") == "Key" for b in bindings.values()),
        "plan declares a BusinessRule Key binding",
    )

    check(data.get("version") == "v3", f"data.version is {data.get('version')!r}, not 'v3'")
    inputs = {i.get("name") for i in data.get("inputs", [])}
    outputs = data.get("outputs", [])
    sources = {o.get("name"): o.get("source") for o in outputs}
    check("creditScore" in inputs, f"input creditScore missing, inputs are {sorted(inputs)}")
    check(sources.get("output") == "=result", f"no output row 'output' with source =result, outputs are {sources}")
    check("Error" in sources, f"output Error missing, outputs are {sorted(sources)}")
    check(
        any(
            o.get("var") == "riskBand" and o.get("source") == "=result.RiskDecision.riskBand" and o.get("type") == "string"
            for o in outputs
        ),
        f"no string output writes =result.RiskDecision.riskBand into riskBand, outputs are {sources}",
    )

    sidecar = json.loads((PROJECT / "bindings_v2.json").read_text())
    check(
        any(r.get("resource") == "BusinessRule" and r.get("key") == RESOURCE_KEY for r in sidecar.get("resources", [])),
        "bindings_v2.json has no BusinessRule resource; run `uip maestro case bindings sync`",
    )

    if failures:
        sys.exit("FAIL: " + "; ".join(failures))
    print("OK: v3 business-rule task bound by name + folderPath, riskBand read from the decision-keyed result")


if __name__ == "__main__":
    main()
