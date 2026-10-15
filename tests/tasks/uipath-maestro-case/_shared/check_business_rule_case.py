#!/usr/bin/env python3
"""BusinessRuleSingleCase: the business-rule task binds the in-solution
CreditRisk rule (resourceKey solution_folder.CreditRisk, empty folderPath),
wires creditScore in and RiskDecision.riskBand out, and debug returns the
rule's LOW_RISK band for the SDD's credit score of 742."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    assert_outputs_contain,
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


def main():
    task = assert_task_type_present("business-rule")
    check_structure(task, get_bindings(read_caseplan()))
    payload = run_debug(timeout=540)
    # 742 >= 700 only reaches LOW_RISK through the rule's decision table.
    assert_outputs_contain(payload, "LOW_RISK")
    print(f"OK: business-rule task bound to in-solution {RULE} "
          f"(displayName={task.get('displayName')!r}); debug Completed with LOW_RISK")


if __name__ == "__main__":
    main()
