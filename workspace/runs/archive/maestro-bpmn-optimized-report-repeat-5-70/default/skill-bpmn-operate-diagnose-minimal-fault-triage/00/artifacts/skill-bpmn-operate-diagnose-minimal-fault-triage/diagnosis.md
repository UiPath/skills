# BPMN Run Diagnosis

**Job:** job-triage-001  
**Instance:** inst-triage-001  
**Folder:** folder-public  
**Final status:** Faulted

---

## Faulting BPMN element

`Task_InvokeLegacyRpa` — `bpmn:serviceTask` invoking `Orchestrator.StartJob`

---

## User-visible symptom

The process started successfully, reached the "Invoke legacy RPA" task, and then
faulted. The variable `triageStatus` was left as `PendingChildProcess`, indicating
the child RPA job was never launched. No further steps executed.

---

## Likely root cause

Incident `inc-triage-001` category **BindingResolution**:

> Resource binding `folderPath` resolved to a folder the process cannot access.

The deployed BPMN binds `folderPath` via `=bindings.LegacyRpaFolder`. The binding
expression resolved (the key exists in the package), but the resolved folder path
names an Orchestrator folder the executing process account cannot access — either
the account is not assigned to that folder, the folder was renamed or deleted after
deployment, or the wrong folder key was recorded in the package metadata.

---

## Fix ownership

| Layer | Implicated? | Action needed |
|---|---|---|
| **BPMN source** | No | The expression `=bindings.LegacyRpaFolder` is the correct pattern; no change needed |
| **Generated package metadata** | Partial | Verify `bindings_v2.json` `LegacyRpaFolder` resource holds the intended target folder path; regenerate if the value is stale |
| **Integration Service enrichment** | No | Not implicated; this is an Orchestrator job invocation, not an IS connector |
| **Cloud configuration** | Yes — primary | The Orchestrator folder referenced by `LegacyRpaFolder` must exist and the executing process account must be assigned to it; correct folder permissions or assignment in Orchestrator |

---

## Safe next operate action

Verify the target Orchestrator folder exists and the process account has access to
it (**Cloud configuration** fix). If the folder path itself is wrong, update
`bindings_v2.json` with the correct folder key and repackage (**Generated package
metadata** fix). Once access is confirmed, a retry of the instance is appropriate
— but retry is an Operate action requiring explicit consent and should not be
taken until the folder access issue is resolved.
