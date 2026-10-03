#!/usr/bin/env python3
"""A business-rule task bound by name + folderPath, mapping the rule's flat v2 outputs."""

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

    inputs = {i.get("name") for i in data.get("inputs", [])}
    outputs = {o.get("name") for o in data.get("outputs", [])}
    check("creditScore" in inputs, f"input creditScore missing, inputs are {sorted(inputs)}")
    check("riskBand" in outputs, f"output riskBand missing, outputs are {sorted(outputs)}")
    check(not any("." in str(name) for name in outputs), f"decision-keyed output names: {sorted(outputs)}")

    sidecar = json.loads((PROJECT / "bindings_v2.json").read_text())
    check(
        any(r.get("resource") == "BusinessRule" and r.get("key") == RESOURCE_KEY for r in sidecar.get("resources", [])),
        "bindings_v2.json has no BusinessRule resource; run `uip maestro case bindings sync`",
    )

    if failures:
        sys.exit("FAIL: " + "; ".join(failures))
    print("OK: business-rule task bound by name + folderPath with flat outputs")


if __name__ == "__main__":
    main()
