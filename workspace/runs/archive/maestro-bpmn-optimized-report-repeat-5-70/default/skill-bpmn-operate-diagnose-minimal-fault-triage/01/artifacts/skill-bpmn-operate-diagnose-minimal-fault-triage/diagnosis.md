# BPMN Run Diagnosis

**Job key:** job-triage-001  
**Instance ID:** inst-triage-001  
**Folder:** folder-public  
**Incident ID:** inc-triage-001

---

## Faulting BPMN element ID

`Task_InvokeLegacyRpa`

---

## User-visible symptom

The process faults immediately after the start event. The instance variable
`triageStatus` is stuck at `PendingChildProcess`, indicating the child RPA job
was never submitted. The run shows status **Faulted** with no downstream
elements reached.

---

## Likely root cause

The task uses an `Orchestrator.StartJob` resource binding. The runtime resolved
the `folderPath` binding to an Orchestrator folder that the process identity
(the account or robot executing the job) does not have permission to access.
This is a **BindingResolution** failure: the binding value itself was resolved
successfully, but the resolved folder is outside the process's access scope in
Orchestrator.

This is not a BPMN structural defect — the element ID and model are intact and
the start event completed normally.

---

## Fix ownership

| Layer | Implicated? | Assessment |
|---|---|---|
| `BPMN source` | No | Element structure and mapping expressions are intact; no authoring change needed. |
| `Generated package metadata` | No | `bindings_v2.json` resource key (`Orchestrator.StartJob`) and binding name (`folderPath`) are correctly wired; no regeneration needed. |
| `Integration Service enrichment` | No | This is an Orchestrator-native resource binding, not an Integration Service connector node. |
| `Cloud configuration` | **Yes** | The `folderPath` binding resolves to an Orchestrator folder the process cannot access. The fix is a cloud-side permission or configuration change: either grant the executing robot/account access to the target folder, or correct the `folderPath` binding value in the process configuration (release/environment parameters) to point to an accessible folder. |

---

## Safe next operate action

**Review and correct the Orchestrator folder permissions or the `folderPath`
parameter value in the cloud process configuration.** Specifically:

1. Confirm which folder the `folderPath` binding resolves to (check the
   release/environment parameter store for this process).
2. Either grant the executing robot/account the required role in that folder, or
   update the `folderPath` value to an Orchestrator folder the process already
   has access to.
3. Once cloud configuration is corrected, a new run can be started — but that
   requires explicit user consent and is outside this diagnostic scope.

No BPMN source edits, package regeneration, or Integration Service enrichment
changes are required.
