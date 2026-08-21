# Fault Diagnosis — job-triage-001 / inst-triage-001

## Faulting BPMN element

**ID:** `Task_InvokeLegacyRpa`  
**Name:** Invoke legacy RPA  
**Type:** `bpmn:serviceTask` → `Orchestrator.StartJob`

## User-visible symptom

The process job reached status **Faulted** at `Task_InvokeLegacyRpa` (72 seconds
into the run). The `triageStatus` variable remained `PendingChildProcess`,
meaning no child RPA job was ever dispatched. Only `Start_Manual` completed
before the fault.

## Likely root cause

Incident `inc-triage-001` (category **BindingResolution**):

> Resource binding `folderPath` resolved to a folder the process cannot access.

The deployed BPMN binds `folderPath` via `=bindings.LegacyRpaFolder`. The
expression evaluated successfully — a folder path was produced — but the
Orchestrator account under which this process runs does not have access to that
folder, so `Orchestrator.StartJob` was rejected before the child job could start.

Two possible root causes, in priority order:

1. **Wrong folder value in `bindings_v2.json`** — `LegacyRpaFolder` resolves to
   a folder path that does not match the intended target folder (e.g., a
   staging path promoted to production without updating the binding).
2. **Missing folder permission in Orchestrator** — the binding resolves to the
   correct folder, but the executing Robot/process account has not been granted
   the required role on that folder in Orchestrator cloud settings.

## Ownership

| Layer | Implicated? | Detail |
|---|---|---|
| `BPMN source` | No | `=bindings.LegacyRpaFolder` expression syntax is correct; the fault is in the resolved value or its access grant, not the BPMN structure. |
| `Generated package metadata` | **Yes (primary candidate)** | `bindings_v2.json` holds the `LegacyRpaFolder` resource value. If the folder path is wrong or points to an inaccessible environment, regenerating / correcting this file and re-packaging is the first fix to attempt. |
| `Integration Service enrichment` | No | This node uses `Orchestrator.StartJob`, not an Integration Service connector; no IS enrichment is involved. |
| `Cloud configuration` | **Yes (secondary candidate)** | If the folder path in `bindings_v2.json` is correct, the executing account needs a folder-level role grant (e.g. Robot Executor) on the target folder in Orchestrator. |

## Safe next operate action

**Do not retry until the binding or permission is corrected.** Retrying against
the same faulted binding will produce the same `BindingResolution` fault.

Recommended next steps (require human action and consent before any cloud change):

1. Inspect `bindings_v2.json` in the package source — confirm the value of the
   `LegacyRpaFolder` resource entry matches the intended Orchestrator folder.
2. If the path is wrong, correct it in `bindings_v2.json`, run
   `scripts/check_metadata_drift.py` to verify no other drift, re-package with
   `uip maestro bpmn pack`, and redeploy.
3. If the path is correct, grant the process account the required folder-level
   role on that folder in Orchestrator cloud settings.
4. After the fix is in place, rerun the process via
   `uip maestro bpmn process run process-invoice-triage --folder-key folder-public`
   (requires explicit user consent).
