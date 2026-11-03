#!/usr/bin/env python3
"""DocumentExtractionCase: the document-extraction task runs the SDD's IXP
deployment in the Case Designer's shape, with the three lines the SDD left
unresolved filled from the tenant, the deployment added to the solution, and
its bindings sidecar entry synced.

No debug: `uip maestro case debug` passes no case inputs, so `fileRef` would be
empty and the task faults `[430002] Invalid input on document extraction
operation`."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import assert_task_type_present, find_caseplan, read_caseplan  # noqa: E402

DEPLOYMENT = "Case Eval Expense"
FOLDER = "Shared"
CONTEXT_ORDER = ["solutionResourceKey", "name", "folderKey", "folderName",
                 "modelName", "modelDisplayName", "digitizationMode"]


def tenant_deployment() -> dict:
    """The deployment as the tenant lists it, read the way the skill is told to."""
    out = subprocess.run(
        ["uip", "solution", "resources", "list", "--kind", "IxpDeployment", "--source", "remote", "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    rows = [r for r in (json.loads(out.stdout).get("Data") or [])
            if r.get("Name") == DEPLOYMENT and r.get("Folder") == FOLDER]
    if len(rows) != 1:
        sys.exit(f"FAIL (fixture): expected one remote IxpDeployment {DEPLOYMENT!r} in {FOLDER!r}, found {len(rows)}.")
    return rows[0]


def check_task(task: dict, plan: dict, remote: dict) -> None:
    data = task.get("data") or {}
    if data.get("serviceType") != "IXP.Extraction" or data.get("version") != "v2":
        sys.exit(f"FAIL: serviceType/version are {data.get('serviceType')!r}/{data.get('version')!r}, expected 'IXP.Extraction'/'v2'.")
    context = data.get("context") or []
    names = [c.get("name") for c in context]
    if names != CONTEXT_ORDER:
        sys.exit(f"FAIL: context entries are {names}, expected the Designer's {CONTEXT_ORDER}.")
    values = {c["name"]: c.get("value") for c in context}
    expected = {
        "solutionResourceKey": remote.get("Key"),
        "folderKey": remote.get("FolderKey"),
        "folderName": FOLDER,
        "modelDisplayName": DEPLOYMENT,
        "digitizationMode": "fileUpload",
    }
    wrong = {k: (values.get(k), v) for k, v in expected.items() if values.get(k) != v}
    if wrong:
        sys.exit(f"FAIL: context values differ from the tenant's deployment (got, expected): {wrong}")
    model = str(values.get("modelName") or "")
    if not model.endswith("-ixp") or model == "":
        sys.exit(f"FAIL: modelName is {model!r}; it must be the deployment's DeploymentName (`<slug>-<hash>-ixp`).")
    projects = subprocess.run(["uip", "ixp", "projects", "list", "--output", "json"], capture_output=True, text=True, timeout=120)
    project_names = {p.get("Name") for p in ((json.loads(projects.stdout).get("Data") or {}).get("Projects") or [])}
    if model in project_names:
        sys.exit(f"FAIL: modelName {model!r} is an IXP project's name; the Designer stores the deployment's DeploymentName.")

    name_ref = str(values.get("name") or "")
    binding_id = name_ref.removeprefix("=bindings.")
    bindings = plan.get("bindings") or []
    binding = next((b for b in bindings if b.get("id") == binding_id), None)
    if binding is None or binding.get("resource") != "ixpDeployment" or binding.get("resourceKey") != remote.get("Key") or binding.get("default") != DEPLOYMENT:
        sys.exit(f"FAIL: context name {name_ref!r} does not reach an ixpDeployment binding keyed {remote.get('Key')!r} defaulting to {DEPLOYMENT!r}: {binding!r}")

    inputs = {i.get("name"): i.get("value") for i in data.get("inputs") or []}
    if inputs.get("fileRef") != "=vars.expenseReceipt":
        sys.exit(f"FAIL: fileRef is {inputs.get('fileRef')!r}, expected the SDD's =vars.expenseReceipt.")
    outputs = sorted(str(o.get("name")).lower() for o in data.get("outputs") or [])
    if outputs != ["error", "output"]:
        sys.exit(f"FAIL: outputs are {outputs}, expected the fixed output and error.")


def check_solution(plan_path: str, remote: dict) -> None:
    project = Path(plan_path).parent
    sidecar = project / "bindings_v2.json"
    if not sidecar.exists() or remote.get("Key") not in sidecar.read_text():
        sys.exit("FAIL: bindings_v2.json has no entry for the deployment; run `uip maestro case bindings sync`.")
    solution = project.parent
    listed = subprocess.run(["uip", "solution", "resources", "list", "--source", "local", "--solution-folder", str(solution), "--output", "json"],
                            capture_output=True, text=True, timeout=120)
    keys = {r.get("Key") for r in (json.loads(listed.stdout).get("Data") or [])}
    if remote.get("Key") not in keys:
        sys.exit("FAIL: the solution does not hold the IXP deployment; `uip solution resources add --source remote --kind IxpDeployment` was not run.")


def main():
    plan_path = find_caseplan("DocumentExtractionCase/**/caseplan.json")
    plan = read_caseplan(plan_path)
    task = assert_task_type_present("document-extraction", caseplan_path=plan_path)
    remote = tenant_deployment()
    check_task(task, plan, remote)
    check_solution(plan_path, remote)
    print(f"OK: document-extraction runs {DEPLOYMENT!r} with the tenant's key, folder and model; "
          "deployment in the solution and the bindings sidecar")


if __name__ == "__main__":
    main()
