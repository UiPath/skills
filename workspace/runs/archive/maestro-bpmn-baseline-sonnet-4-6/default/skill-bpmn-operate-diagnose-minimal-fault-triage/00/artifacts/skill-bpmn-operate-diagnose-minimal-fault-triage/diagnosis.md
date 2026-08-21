# Diagnosis: job-triage-001 / inst-triage-001

## Faulting BPMN element

**Element ID:** `Task_InvokeLegacyRpa`  
**Element type:** `bpmn:serviceTask` (Orchestrator.StartJob)

## User-visible symptom

The process run faulted immediately after start. The instance cursor is stuck at
`Task_InvokeLegacyRpa` in state `Faulted` and the job status is `Faulted`.
No downstream work was attempted; `triageStatus` remained `PendingChildProcess`.

## Likely root cause

Incident `inc-triage-001` category `BindingResolution`:

> "Resource binding 'folderPath' resolved to a folder the process cannot access."

The deployed BPMN contains:

```xml
<uipath:binding name="folderPath" expression="=bindings.LegacyRpaFolder"/>
```

The binding expression is syntactically correct and resolved at runtime to a
folder path value. However, the resolved Orchestrator folder is inaccessible to
the executing process. The runtime could look up the folder but could not
dispatch the job into it — this is an access/permission failure, not a missing
binding value.

## Ownership

| Layer | Implicated? | Rationale |
|---|---|---|
| `BPMN source` | **No** | `=bindings.LegacyRpaFolder` is valid syntax; the expression and mapping are correct. |
| `Generated package metadata` | **Possible** | If `bindings_v2.json` resolved `LegacyRpaFolder` to the wrong folder key, the correct folder may never have been targeted. Verify the resolved path in the package. |
| `Integration Service enrichment` | **No** | This node uses `Orchestrator.StartJob`, not an Integration Service connector; no IS enrichment is involved. |
| `Cloud configuration` | **Primary** | The binding resolved successfully to a folder value, but the process account lacks permission to start jobs in that Orchestrator folder. Folder-level role assignment or the binding's target folder key needs correction in Orchestrator cloud. |

## Safe next operate action

Inspect the Orchestrator folder that `LegacyRpaFolder` resolves to and confirm
whether the process robot account holds the `Jobs: Create` (or equivalent)
permission on that folder. If the folder key is wrong, update the folder
assignment in the cloud release/binding configuration (`Cloud configuration`).
If the key is correct but permissions are missing, grant the appropriate role to
the robot account on that folder (`Cloud configuration`). No BPMN source edits
are required.

Do **not** retry until the folder access issue is resolved; the retry would fault
on the same element for the same reason.
