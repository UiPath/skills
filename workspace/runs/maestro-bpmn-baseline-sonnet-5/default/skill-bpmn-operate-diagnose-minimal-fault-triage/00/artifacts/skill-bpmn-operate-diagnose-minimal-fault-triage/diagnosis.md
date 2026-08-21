# Fault Diagnosis — job-triage-001 / inst-triage-001

## Context
- Job key: `job-triage-001`
- Instance id: `inst-triage-001`
- Folder key: `folder-public`
- Process key: `process-invoice-triage`
- Job status: `Faulted` (started 2026-05-01T12:00:00Z, ended 2026-05-01T12:01:12Z)

## Faulting BPMN element
- Element id: **`Task_InvokeLegacyRpa`** (service task "Invoke legacy RPA", `uipath:activity service="Orchestrator.StartJob"`)
- Confirmed via `instance incidents`, `element-executions` (state `Faulted`, the only non-`Completed` element after `Start_Manual`), and `instance cursors` (halted at this element). The deployed BPMN asset (`instance asset`) confirms this element is a `bpmn:serviceTask` whose extension binds `folderPath` to `=bindings.LegacyRpaFolder`.

## User-visible symptom
The process run ends in a `Faulted` status shortly after starting (~72s), with an incident (`inc-triage-001`, category `BindingResolution`) reported against `Task_InvokeLegacyRpa`. Runtime variables show the process stalled with `triageStatus = "PendingChildProcess"` — the legacy RPA job invocation never completed.

## Likely root cause
The incident message states: *"Resource binding 'folderPath' resolved to a folder the process cannot access."* The `folderPath` binding on the `Orchestrator.StartJob` resource (see `safeDetails.resourceKey = Orchestrator.StartJob`, `bindingName = folderPath`) evaluated successfully as an expression (`=bindings.LegacyRpaFolder`), but the folder it resolved to is not one the running process/service account has access to in this environment. This is a target-environment folder binding/permission mismatch, not a malformed BPMN expression or missing extension payload — the BPMN source and its binding expression are structurally correct.

## Ownership of the fix
**Cloud configuration** — the binding resolved as designed; the problem is that the bound Orchestrator folder is inaccessible to the process's execution context in this environment (a folder/access choice on the deployed environment), not a defect in the BPMN model, the generated package metadata's binding wiring, or an Integration Service connector enrichment (this activity is a native `Orchestrator.StartJob`, not an `Intsvc.*` connector node).

Not implicated:
- `BPMN source` — the service task and its `folderPath` binding expression are well-formed and resolve without error.
- `Generated package metadata` — no evidence of a stale/missing entry in bindings/entry-point/package-descriptor wiring; the binding itself resolves, it just points at an inaccessible folder.
- `Integration Service enrichment` — not applicable; the faulting node is a native Orchestrator activity, not an IS connector element.

## Safe next operate action
Do not retry, cancel, or migrate the instance. The safe next step is a **cloud configuration review**: have an environment/folder administrator verify and correct the Orchestrator folder access grant (read/execute permissions for the process's service account or robot identity) on the folder that the `folderPath` binding resolves to for this environment. Only after that access grant is confirmed corrected should an authorized operator consider re-running the process.
