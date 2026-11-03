#!/usr/bin/env python3
"""BusinessRuleSingleCase: the business-rule task binds the in-solution
CreditRisk rule (resourceKey solution_folder.CreditRisk, empty folderPath),
wires creditScore in and RiskDecision.riskBand out, and the debugged
case runs the rule task to completion."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_task_type_present,
    get_bindings,
    read_caseplan,
    run_debug,
    task_is_skeleton,
)

RULE = "CreditRisk"
RESOURCE_KEY = f"solution_folder.{RULE}"


def _binding_for(ref: object, bindings: list[dict]) -> dict:
    if not isinstance(ref, str) or not ref.startswith("=bindings."):
        sys.exit(f"FAIL: business-rule task reference {ref!r} is not a =bindings.<id> reference.")
    binding_id = ref[len("=bindings."):]
    for b in bindings:
        if b.get("id") == binding_id:
            return b
    sys.exit(f"FAIL: business-rule task references binding {binding_id!r}, which is not in bindings[].")


def check_structure(task: dict, bindings: list[dict]) -> None:
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: business-rule task is a placeholder: data.name and data.folderPath are unset. "
            "CreditRisk is an in-solution sibling; `registry search --local` finds it."
        )
    data = task.get("data") or {}
    name_b = _binding_for(data.get("name"), bindings)
    folder_b = _binding_for(data.get("folderPath"), bindings)
    for label, b in (("name", name_b), ("folderPath", folder_b)):
        if b.get("resource") != "BusinessRule" or b.get("resourceKey") != RESOURCE_KEY:
            sys.exit(
                f"FAIL: {label} binding is resource={b.get('resource')!r} resourceKey={b.get('resourceKey')!r}; "
                f"an in-solution rule binds resource 'BusinessRule', resourceKey {RESOURCE_KEY!r}."
            )
    if name_b.get("default") != RULE:
        sys.exit(f"FAIL: name binding default is {name_b.get('default')!r}, expected {RULE!r}.")
    if folder_b.get("default") not in ("", None):
        sys.exit(
            f"FAIL: folderPath binding default is {folder_b.get('default')!r}. An in-solution rule runs "
            "from the case's own folder, so folderPath is empty; the solution_folder sentinel there "
            "fails at runtime with 'Folder does not exist'."
        )

    inputs = {i.get("name"): i.get("value") for i in data.get("inputs") or []}
    if inputs.get("creditScore") != "=vars.creditScore":
        sys.exit(f"FAIL: input creditScore is {inputs.get('creditScore')!r}, expected '=vars.creditScore'.")
    extract = [o for o in data.get("outputs") or [] if o.get("source") == "=RiskDecision.riskBand"]
    if not extract or extract[0].get("var") != "riskBand":
        sys.exit(
            "FAIL: no output row writes =RiskDecision.riskBand to the riskBand case variable "
            f"(outputs: {[(o.get('name'), o.get('var'), o.get('source')) for o in data.get('outputs') or []]})."
        )


def assert_task_completed(payload: dict, task: dict) -> None:
    """Case debug reports element executions, not variable values, so the task's
    own execution reaching Completed is what the run can prove."""
    executions = _get_ci(payload, "elementExecutions", "ElementExecutions") or []
    runs = [e for e in executions if _get_ci(e, "elementId", "ElementId") == task.get("id")]
    if not runs:
        sys.exit(f"FAIL: debug has no execution for task {task.get('displayName')!r} (id {task.get('id')!r}).")
    status = _get_ci(runs[-1], "status", "Status")
    if status not in ("Completed", "Successful"):
        sys.exit(f"FAIL: debug execution for task {task.get('displayName')!r} finished {status!r}.")


def main():
    task = assert_task_type_present("business-rule")
    check_structure(task, get_bindings(read_caseplan()))
    payload = run_debug(timeout=540)
    assert_task_completed(payload, task)
    print(f"OK: business-rule task bound to in-solution {RULE} "
          f"(displayName={task.get('displayName')!r}); debug Completed, rule task executed")


if __name__ == "__main__":
    main()
