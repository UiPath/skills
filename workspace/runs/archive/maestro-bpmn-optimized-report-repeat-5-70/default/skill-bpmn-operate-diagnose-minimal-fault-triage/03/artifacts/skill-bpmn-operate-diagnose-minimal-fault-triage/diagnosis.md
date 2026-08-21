# Diagnosis — job-triage-001 / inst-triage-001

## Faulting BPMN element

**Element ID:** `Task_InvokeLegacyRpa`  
**Element name:** Invoke legacy RPA  
**Service:** `Orchestrator.StartJob`

## User-visible symptom

The process run faulted 72 seconds after start. The task that invokes the
downstream RPA job never launched; the incident reported:

> Resource binding 'folderPath' resolved to a folder the process cannot access.

The runtime variable `triageStatus` was left at `PendingChildProcess`, meaning
no child job was ever dispatched.

## Likely root cause

The deployed BPMN reads:

```xml
<uipath:binding name="folderPath" expression="=bindings.LegacyRpaFolder"/>
```

The expression syntax is valid — `=bindings.LegacyRpaFolder` is correctly
formed and the key `LegacyRpaFolder` was found in the binding resources
(the incident category is `BindingResolution`, not `BindingNotFound`). However,
the folder path that the binding resolves to at runtime is either:

1. set to a folder the process account has no Execute permission on, **or**
2. set to a folder that does not exist in the target Orchestrator tenant.

The binding value itself lives in the generated `bindings_v2.json` resource
entry for `LegacyRpaFolder`. No other element executed after the start event,
confirming the fault originated here and is not downstream noise.

## Fix ownership

| Layer | Implicated? | Detail |
|---|---|---|
| **BPMN source** | No | The expression `=bindings.LegacyRpaFolder` is syntactically correct; no change needed in the `.bpmn` file. |
| **Generated package metadata** | **Yes — primary fix** | `bindings_v2.json` must be corrected so the `LegacyRpaFolder` resource points to an Orchestrator folder that the process account can access. Re-run CLI enrichment (`uip maestro bpmn registry get` + `--connection-id`/resource enrichment) and regenerate the package. |
| **Integration Service enrichment** | No | `Orchestrator.StartJob` is a built-in Orchestrator resource, not an Integration Service connector; no IS enrichment is involved. |
| **Cloud configuration** | Possible — secondary check | If the target folder path in `bindings_v2.json` is correct but the process account (robot or service account) lacks the Execute permission on that folder, the folder's role assignment must be updated in Orchestrator tenant settings. |

## Safe next operate action

1. Inspect `bindings_v2.json` in the project directory; locate the
   `LegacyRpaFolder` resource entry and verify the folder path value.
2. If the path is wrong: correct it, re-enrich with the CLI, and repackage.
3. If the path is correct: verify in Orchestrator that the process account has
   the **Execute** role (or equivalent) on that folder, and correct the role
   assignment if it is missing.
4. After the package or role is corrected, republish and re-run the process.

Do **not** retry the current faulted instance — the binding will resolve to
the same inaccessible folder and fault again.
