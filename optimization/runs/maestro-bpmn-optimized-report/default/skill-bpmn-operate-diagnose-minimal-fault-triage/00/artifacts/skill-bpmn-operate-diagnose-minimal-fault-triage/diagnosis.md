# Diagnosis — job-triage-001 / inst-triage-001

## Faulting BPMN element

**`Task_InvokeLegacyRpa`** ("Invoke legacy RPA")  
Service: `Orchestrator.StartJob`

## User-visible symptom

The process faulted 72 seconds after start.  
Runtime variable `triageStatus` is frozen at `"PendingChildProcess"`, meaning no
child RPA job was ever enqueued.  
Incident `inc-triage-001` (category `BindingResolution`):
> "Resource binding 'folderPath' resolved to a folder the process cannot access."

## Likely root cause

The deployed BPMN drives `folderPath` through the binding expression
`=bindings.LegacyRpaFolder` (from `bindings_v2.json`).  
The binding resolved at runtime — the value is present — but the Orchestrator
folder it resolves to rejected the start-job call.  
Two sub-causes, in probability order:

1. **Wrong folder path value in `bindings_v2.json`** — `LegacyRpaFolder` was
   scaffolded with a placeholder or a stale environment path that does not match
   a real, accessible folder in the target tenant.
2. **Correct path, missing permission** — the folder exists but the
   robot/process account executing the job lacks the "View / Edit / Create Jobs"
   permission on that folder.

## Ownership

| Label | Implicated? | Reason |
|---|---|---|
| `BPMN source` | **No** | The binding expression `=bindings.LegacyRpaFolder` is the correct pattern; no structural defect in the `.bpmn`. |
| `Generated package metadata` | **Yes (primary candidate)** | If `bindings_v2.json` carries an incorrect or placeholder folder path for `LegacyRpaFolder`, regenerating / correcting the binding value fixes the fault. |
| `Integration Service enrichment` | **No** | `Orchestrator.StartJob` is a native Orchestrator resource; no IS connector enrichment is involved. |
| `Cloud configuration` | **Yes (secondary candidate)** | If the folder path in `bindings_v2.json` is correct, the fix is granting the executing robot/process account the required folder-level permissions in Orchestrator. |

## Safe next operate action

1. **Inspect `bindings_v2.json`** — find the `LegacyRpaFolder` resource entry
   and verify its folder path value against the target Orchestrator tenant.
   - If the value is wrong or a placeholder → correct it and repackage
     (`Generated package metadata` fix).
   - If the value is correct → grant the executing account folder permissions
     in Orchestrator (`Cloud configuration` fix).
2. No retry, cancel, cursor move, or re-deploy should be attempted until the
   root cause is confirmed and the appropriate fix is applied.
